import { useRef } from 'react';

import { zodResolver } from '@hookform/resolvers/zod';
import type { TurnstileInstance } from '@marsidev/react-turnstile';
import { Loader2Icon, MailIcon, SendIcon } from 'lucide-react';
import { useForm } from 'react-hook-form';
import { toast } from 'sonner';
import { z } from 'zod';

import { miscApi } from 'api/http';
import SectionHeading from 'site/components/home/SectionHeading';
import Turnstile, { CAPTCHA_FAILED } from 'site/components/Turnstile';
import { Button } from 'site/components/ui/button';
import {
  Field,
  FieldError,
  FieldGroup,
  FieldLabel,
} from 'site/components/ui/field';
import { Input } from 'site/components/ui/input';
import { Textarea } from 'site/components/ui/textarea';
import { getApiErrorMessage, isRateLimited } from 'site/lib/apiError';

const contactSchema = z.object({
  email: z.email('Érvényes e-mail-címet adj meg!'),
  message: z.string().trim().min(1, 'Írd meg, miben segíthetünk!'),
  name: z
    .string()
    .trim()
    .min(1, 'Add meg a neved!')
    .max(150, 'Legfeljebb 150 karakter lehet.'),
});

type ContactValues = z.infer<typeof contactSchema>;

function ContactForm() {
  const turnstile = useRef<TurnstileInstance>(null);
  const {
    formState: { errors, isSubmitting },
    handleSubmit,
    register,
    reset,
  } = useForm<ContactValues>({
    defaultValues: { email: '', message: '', name: '' },
    resolver: zodResolver(contactSchema),
  });

  const onSubmit = async (values: ContactValues) => {
    const captcha = await turnstile.current
      ?.getResponsePromise()
      .catch(() => null);
    if (!captcha) {
      toast.error('Nem sikerült elküldeni az üzenetet.', {
        description: CAPTCHA_FAILED,
      });
      return;
    }
    try {
      await miscApi.miscContactCreate({ ...values, captcha });
      toast.success('Köszönjük, megkaptuk az üzeneted!');
      reset();
    } catch (error) {
      toast.error('Nem sikerült elküldeni az üzenetet.', {
        description: isRateLimited(error)
          ? 'Túl sok üzenetet küldtél. Próbáld újra később!'
          : getApiErrorMessage(error),
      });
    } finally {
      // A token is only valid for one request.
      turnstile.current?.reset();
    }
  };

  return (
    <form
      className="rounded-3xl border bg-card p-6 shadow-sm sm:p-8"
      noValidate
      onSubmit={(event) => void handleSubmit(onSubmit)(event)}
    >
      <FieldGroup>
        <div className="grid gap-5 sm:grid-cols-2">
          <Field data-invalid={!!errors.name}>
            <FieldLabel htmlFor="contact-name">Név</FieldLabel>
            <Input
              aria-invalid={!!errors.name}
              autoComplete="name"
              id="contact-name"
              placeholder="Teljes neved"
              {...register('name')}
            />
            <FieldError errors={[errors.name]} />
          </Field>
          <Field data-invalid={!!errors.email}>
            <FieldLabel htmlFor="contact-email">E-mail-cím</FieldLabel>
            <Input
              aria-invalid={!!errors.email}
              autoComplete="email"
              id="contact-email"
              placeholder="nev@example.com"
              type="email"
              {...register('email')}
            />
            <FieldError errors={[errors.email]} />
          </Field>
        </div>
        <Field data-invalid={!!errors.message}>
          <FieldLabel htmlFor="contact-message">Üzenet</FieldLabel>
          <Textarea
            aria-invalid={!!errors.message}
            className="min-h-36"
            id="contact-message"
            placeholder="Miben segíthetünk?"
            {...register('message')}
          />
          <FieldError errors={[errors.message]} />
        </Field>
        <Turnstile ref={turnstile} />
        <Button
          className="w-full sm:w-auto sm:self-start"
          disabled={isSubmitting}
          size="lg"
          type="submit"
        >
          {isSubmitting ? (
            <Loader2Icon className="animate-spin" data-icon="inline-start" />
          ) : (
            <SendIcon data-icon="inline-start" />
          )}
          Üzenet küldése
        </Button>
      </FieldGroup>
    </form>
  );
}

export default function ContactSection() {
  return (
    <section className="scroll-mt-16 py-24 sm:py-32" id="kapcsolat">
      <div className="mx-auto grid max-w-6xl gap-12 px-4 sm:px-6 lg:grid-cols-[1fr_1.15fr] lg:gap-20">
        <div>
          <SectionHeading kicker="Kapcsolat" title="Kérdésed van?">
            Ha nem találod a választ, vagy más ügyben keresnél minket, írj
            nekünk itt, vagy küldj e&#8209;mailt.
          </SectionHeading>
          <a
            className="group mt-8 inline-flex items-center gap-4 rounded-2xl border bg-card p-4 pr-6 transition hover:border-primary/40 hover:shadow-md"
            href="mailto:info@bsstudio.hu"
          >
            <span className="grid size-11 place-items-center rounded-xl bg-primary/10 text-primary transition-colors group-hover:bg-primary group-hover:text-primary-foreground">
              <MailIcon className="size-5" />
            </span>
            <span>
              <span className="block text-sm text-muted-foreground">
                E-mail
              </span>
              <span className="font-medium">info@bsstudio.hu</span>
            </span>
          </a>
        </div>
        <ContactForm />
      </div>
    </section>
  );
}
