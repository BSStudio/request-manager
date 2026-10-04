import { useEffect, useMemo, useRef, useState } from 'react';

import type { TurnstileInstance } from '@marsidev/react-turnstile';
import { useQuery } from '@tanstack/react-query';
import { parsePhoneNumberFromString } from 'libphonenumber-js';
import {
  ArrowLeftIcon,
  ArrowRightIcon,
  ClockIcon,
  Loader2Icon,
  RotateCcwIcon,
  SendIcon,
} from 'lucide-react';
import {
  type FieldErrors,
  FormProvider,
  type Resolver,
  useForm,
  useFormContext,
  useWatch,
} from 'react-hook-form';
import { useNavigate } from 'react-router';
import { toast } from 'sonner';
import type { ZodType } from 'zod';

import { requestsApi } from 'api/http';
import PageHero from 'site/components/PageHero';
import EventStep from 'site/components/request-form/EventStep';
import NotesStep from 'site/components/request-form/NotesStep';
import PersonalStep from 'site/components/request-form/PersonalStep';
import {
  emptyValues,
  eventSchema,
  notesSchema,
  OTHER_TYPE,
  personalSchema,
  type RequestFormValues,
  toDateTime,
} from 'site/components/request-form/schema';
import {
  type StepInfo,
  StepList,
  StepProgress,
} from 'site/components/request-form/StepIndicator';
import SuccessView from 'site/components/request-form/SuccessView';
import SummaryStep, {
  type Requester,
} from 'site/components/request-form/SummaryStep';
import Turnstile, { CAPTCHA_FAILED } from 'site/components/Turnstile';
import { Button } from 'site/components/ui/button';
import { usePageTitle } from 'site/hooks/usePageTitle';
import { getApiErrorMessage, isRateLimited } from 'site/lib/apiError';
import { meQuery } from 'site/lib/queries';
import { useSessionUser } from 'site/lib/session';

type StepKey = 'event' | 'notes' | 'personal' | 'summary';

const stepInfo: Record<StepKey, StepInfo> = {
  event: {
    description: 'Időpont, helyszín, videó típusa',
    title: 'Az esemény',
  },
  notes: {
    description: 'Minden, amit még tudnunk kell',
    title: 'Megjegyzés',
  },
  personal: { description: 'Név és elérhetőség', title: 'Adataid' },
  summary: { description: 'Ellenőrzés és beküldés', title: 'Összegzés' },
};

const stepSchemas: Partial<Record<StepKey, ZodType>> = {
  event: eventSchema,
  notes: notesSchema,
  personal: personalSchema,
};

// Keeps the answers if the page is reloaded halfway through.
const DRAFT_KEY = 'request-draft';

function loadDraft(): RequestFormValues {
  try {
    const draft = sessionStorage.getItem(DRAFT_KEY);
    return draft
      ? { ...emptyValues, ...(JSON.parse(draft) as Partial<RequestFormValues>) }
      : emptyValues;
  } catch {
    return emptyValues;
  }
}

// Validates only the fields of the step on screen.
const stepResolver: Resolver<RequestFormValues, { step: StepKey }> = (
  values,
  context,
) => {
  const result = context && stepSchemas[context.step]?.safeParse(values);
  if (!result || result.success) return { errors: {}, values };

  const errors: FieldErrors<RequestFormValues> = {};
  for (const issue of result.error.issues) {
    const name = issue.path[0] as keyof RequestFormValues;
    errors[name] ??= { message: issue.message, type: issue.code };
  }
  return { errors, values: {} };
};

// Validating on blur would move the layout under the pointer between mousedown
// and click, so errors only appear on "Tovább" and then follow the answers.
function LiveValidation() {
  const { trigger } = useFormContext<RequestFormValues>();
  const values = useWatch<RequestFormValues>();

  useEffect(() => {
    void trigger();
  }, [trigger, values]);

  return null;
}

function NewRequestPage() {
  usePageTitle('Felkérés beküldése');
  const navigate = useNavigate();
  const user = useSessionUser();
  const me = useQuery({ ...meQuery(), enabled: !!user });
  const steps = useMemo<StepKey[]>(
    () =>
      user
        ? ['event', 'notes', 'summary']
        : ['personal', 'event', 'notes', 'summary'],
    [user],
  );
  const [stepIndex, setStepIndex] = useState(0);
  const current = Math.min(stepIndex, steps.length - 1);
  const step = steps[current];
  const [initialValues] = useState(loadDraft);
  const form = useForm<RequestFormValues, { step: StepKey }>({
    context: { step },
    defaultValues: initialValues,
    resolver: stepResolver,
  });
  const [attemptedStep, setAttemptedStep] = useState<StepKey | null>(null);
  const answers = useWatch({ control: form.control });
  const hasAnswers = Object.values(answers).some(Boolean);
  const turnstile = useRef<TurnstileInstance>(null);
  const [submitting, setSubmitting] = useState(false);
  const [createdId, setCreatedId] = useState<number | null>(null);
  const card = useRef<HTMLDivElement>(null);

  useEffect(
    () =>
      form.subscribe({
        callback: ({ values }) => {
          try {
            sessionStorage.setItem(DRAFT_KEY, JSON.stringify(values));
          } catch {
            // Storage can be unavailable, the form works without the draft.
          }
        },
        formState: { values: true },
      }),
    [form],
  );

  // Requests are made in the user's name, so the profile has to be complete.
  useEffect(() => {
    if (!me.data) return;
    const { email, first_name, last_name, profile } = me.data;
    const missing = [
      !last_name && 'vezetéknév',
      !first_name && 'keresztnév',
      !email && 'e-mail-cím',
      !profile.phone_number && 'telefonszám',
    ].filter(Boolean);
    if (missing.length) {
      toast.warning('Előbb egészítsd ki a profilodat!', {
        description: `Hiányzik: ${missing.join(', ')}.`,
        id: 'profile-incomplete',
      });
      void navigate('/profile', { replace: true });
    }
  }, [me.data, navigate]);

  const requester: Requester | null = me.data
    ? {
        email: me.data.email ?? '',
        name: `${me.data.last_name ?? ''} ${me.data.first_name ?? ''}`.trim(),
        phone:
          parsePhoneNumberFromString(
            me.data.profile.phone_number ?? '',
          )?.formatInternational() ??
          me.data.profile.phone_number ??
          '',
      }
    : null;

  const goTo = (index: number) => {
    setStepIndex(index);
    card.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  const next = async () => {
    if (await form.trigger(undefined, { shouldFocus: true })) goTo(current + 1);
    else setAttemptedStep(step);
  };

  const submit = async () => {
    const values = form.getValues();
    const start = toDateTime(values.startDate, values.startTime);
    const end = toDateTime(values.endDate, values.endTime);
    if (!start || !end) return;

    setSubmitting(true);
    const captcha = user
      ? undefined
      : await turnstile.current?.getResponsePromise().catch(() => null);
    if (captcha === null) {
      toast.error('Nem sikerült beküldeni a felkérést.', {
        description: CAPTCHA_FAILED,
      });
      setSubmitting(false);
      return;
    }
    try {
      const { data } = await requestsApi.requestsCreate({
        comment: values.comment.trim(),
        end_datetime: end.toISOString(),
        place: values.place.trim(),
        start_datetime: start.toISOString(),
        title: values.title.trim(),
        type:
          values.type === OTHER_TYPE ? values.typeOther.trim() : values.type,
        ...(!user && {
          captcha,
          requester_email: values.requesterEmail.trim(),
          requester_first_name: values.requesterFirstName.trim(),
          requester_last_name: values.requesterLastName.trim(),
          requester_mobile:
            parsePhoneNumberFromString(values.requesterMobile, 'HU')?.number ??
            values.requesterMobile,
        }),
      });
      sessionStorage.removeItem(DRAFT_KEY);
      setCreatedId(data.id);
      card.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    } catch (error) {
      toast.error('Nem sikerült beküldeni a felkérést.', {
        description: isRateLimited(error)
          ? 'Túl sok felkérést küldtél. Próbáld újra később!'
          : getApiErrorMessage(error),
      });
    } finally {
      setSubmitting(false);
      // A Turnstile token is only valid for one request.
      turnstile.current?.reset();
    }
  };

  const startOver = () => {
    form.reset(emptyValues);
    setAttemptedStep(null);
    setCreatedId(null);
    setStepIndex(0);
  };

  const restart = () => {
    const previous = { index: current, values: form.getValues() };
    startOver();
    toast('Kiürítettük az űrlapot.', {
      action: {
        label: 'Visszavonás',
        onClick: () => {
          form.reset(previous.values);
          setStepIndex(previous.index);
        },
      },
    });
  };

  const loading = !!user && me.isPending;
  const isSummary = step === 'summary';

  return (
    <>
      <PageHero kicker="Új felkérés" title="Mesélj az eseményedről!">
        <p className="mt-4 max-w-xl text-lg text-white/70">
          Néhány pillanat az egész. Minél több részletet adsz meg, annál
          könnyebben tudunk tervezni.
        </p>
      </PageHero>
      <div className="relative z-10 mx-auto -mt-16 grid w-full max-w-6xl items-start gap-8 px-4 pb-24 sm:px-6 lg:grid-cols-[17rem_1fr] lg:gap-12">
        <aside className="sticky top-24 hidden lg:block">
          <div className="rounded-3xl border bg-card p-6 shadow-sm">
            <StepList
              current={createdId ? steps.length : current}
              onSelect={goTo}
              steps={steps.map((key) => stepInfo[key])}
            />
          </div>
          <p className="mt-6 flex gap-2 px-2 text-sm text-muted-foreground">
            <ClockIcon className="mt-0.5 size-4 shrink-0" />
            Legalább 8 nappal az esemény előtt, hétfőig küldd be.
          </p>
        </aside>
        <div
          className="min-w-0 scroll-mt-24 rounded-3xl border bg-card p-6 shadow-sm sm:p-8"
          ref={card}
        >
          {createdId && (
            <SuccessView
              onNewRequest={startOver}
              requestId={user ? createdId : null}
            />
          )}
          {!createdId && loading && (
            <div className="grid place-items-center py-24">
              <Loader2Icon className="size-8 animate-spin text-muted-foreground" />
            </div>
          )}
          {!createdId && !loading && (
            <FormProvider {...form}>
              {attemptedStep === step && <LiveValidation />}
              <form
                noValidate
                onSubmit={(event) => {
                  event.preventDefault();
                  void (isSummary ? submit() : next());
                }}
              >
                <div className="flex min-h-8 items-center justify-between gap-4">
                  <h2 className="text-lg font-semibold lg:text-2xl lg:font-bold">
                    {stepInfo[step].title}
                  </h2>
                  {hasAnswers && (
                    <Button
                      className="-mr-3"
                      disabled={submitting}
                      onClick={restart}
                      size="sm"
                      type="button"
                      variant="ghost"
                    >
                      <RotateCcwIcon data-icon="inline-start" />
                      Újrakezdés
                    </Button>
                  )}
                </div>
                <div className="mt-4 lg:hidden">
                  <StepProgress
                    current={current}
                    steps={steps.map((key) => stepInfo[key])}
                  />
                </div>
                <div
                  className="mt-6 animate-in duration-300 fade-in slide-in-from-right-4"
                  key={step}
                >
                  {step === 'personal' && <PersonalStep />}
                  {step === 'event' && <EventStep />}
                  {step === 'notes' && <NotesStep />}
                  {isSummary && (
                    <SummaryStep
                      onEdit={(target) => goTo(steps.indexOf(target))}
                      requester={requester}
                    >
                      {!user && <Turnstile ref={turnstile} />}
                    </SummaryStep>
                  )}
                </div>
                <div className="sticky bottom-0 z-10 -mx-6 mt-8 flex gap-3 border-t bg-card/95 px-6 pt-4 pb-[calc(1rem+env(safe-area-inset-bottom))] backdrop-blur sm:static sm:mx-0 sm:border-0 sm:bg-transparent sm:p-0 sm:backdrop-blur-none">
                  {current > 0 && (
                    <Button
                      onClick={() => goTo(current - 1)}
                      size="lg"
                      type="button"
                      variant="outline"
                    >
                      <ArrowLeftIcon data-icon="inline-start" />
                      Vissza
                    </Button>
                  )}
                  <Button
                    className="ml-auto"
                    disabled={submitting}
                    size="lg"
                    type="submit"
                  >
                    {isSummary ? (
                      <>
                        {submitting ? (
                          <Loader2Icon
                            className="animate-spin"
                            data-icon="inline-start"
                          />
                        ) : (
                          <SendIcon data-icon="inline-start" />
                        )}
                        Beküldés
                      </>
                    ) : (
                      <>
                        Tovább
                        <ArrowRightIcon data-icon="inline-end" />
                      </>
                    )}
                  </Button>
                </div>
              </form>
            </FormProvider>
          )}
        </div>
      </div>
    </>
  );
}

export { NewRequestPage as Component };
