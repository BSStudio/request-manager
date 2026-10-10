import { zodResolver } from '@hookform/resolvers/zod';
import { isAxiosError } from 'axios';
import { parsePhoneNumberFromString } from 'libphonenumber-js';
import { InfoIcon, Loader2Icon, TriangleAlertIcon } from 'lucide-react';
import { useForm } from 'react-hook-form';
import { useNavigate } from 'react-router';
import { toast } from 'sonner';
import { z } from 'zod';

import { getApiErrorMessage } from 'api/errors';
import { meApi } from 'api/http';
import type { User } from 'api/models';
import { formatName } from 'helpers/names';
import { formatPhone, toE164 } from 'helpers/phone';
import { cacheUser } from 'helpers/session';
import { Button } from 'site/components/ui/button';
import {
  Field,
  FieldDescription,
  FieldError,
  FieldGroup,
  FieldLabel,
} from 'site/components/ui/field';
import { Input } from 'site/components/ui/input';
import {
  emailSchema,
  getMissingProfileFields,
  nameSchema,
  phoneSchema,
} from 'site/lib/person';

const profileSchema = z.object({
  email: emailSchema,
  first_name: nameSchema('Add meg a keresztneved!'),
  last_name: nameSchema('Add meg a vezetékneved!'),
  phone_number: phoneSchema,
});

type ProfileValues = z.infer<typeof profileSchema>;

function toValues(user: User): ProfileValues {
  return {
    email: user.email ?? '',
    first_name: user.first_name ?? '',
    last_name: user.last_name ?? '',
    phone_number: user.phone_number ? formatPhone(user.phone_number) : '',
  };
}

function ReadOnlyDetails({ user }: { user: User }) {
  const values = toValues(user);
  const rows = [
    {
      label: 'Név',
      value: formatName(values.last_name, values.first_name),
    },
    { label: 'E-mail-cím', value: values.email },
    { label: 'Telefonszám', value: values.phone_number },
  ];

  return (
    <>
      <dl className="grid gap-x-6 gap-y-3 text-sm sm:grid-cols-[auto_1fr]">
        {rows.map(({ label, value }) => (
          <div className="contents" key={label}>
            <dt className="text-muted-foreground">{label}</dt>
            <dd>{value || '–'}</dd>
          </div>
        ))}
      </dl>
      <p className="mt-6 flex gap-3 rounded-2xl bg-muted/50 px-4 py-3 text-sm leading-relaxed">
        <InfoIcon className="mt-0.5 size-4 shrink-0 text-primary" />
        Az adataid a BSS címtárából jönnek, ott tudod módosítani őket.
      </p>
    </>
  );
}

export default function PersonalDetails({ user }: { user: User }) {
  const navigate = useNavigate();
  const incomplete = getMissingProfileFields(user).length > 0;
  const {
    formState: { errors, isDirty, isSubmitting },
    handleSubmit,
    register,
    reset,
    setError,
    setValue,
  } = useForm<ProfileValues>({
    defaultValues: toValues(user),
    resolver: zodResolver(profileSchema),
  });

  if (user.role !== 'user') return <ReadOnlyDetails user={user} />;

  const onSubmit = async (values: ProfileValues) => {
    try {
      const { data } = await meApi.mePartialUpdate({
        email: values.email,
        first_name: values.first_name,
        last_name: values.last_name,
        phone_number: toE164(values.phone_number),
      });
      cacheUser(data);
      reset(toValues(data));
      if (incomplete) {
        toast.success('Elmentettük az adataidat.', {
          action: {
            label: 'Tovább a felkéréshez',
            onClick: () => void navigate('/new-request'),
          },
          duration: 10000,
        });
      } else {
        toast.success('Elmentettük az adataidat.');
      }
    } catch (error) {
      const fields = isAxiosError(error)
        ? (error.response?.data as
            Partial<Record<keyof ProfileValues, string[]>> | undefined)
        : undefined;
      const fieldErrors = {
        email: fields?.email?.[0],
        first_name: fields?.first_name?.[0],
        last_name: fields?.last_name?.[0],
        phone_number: fields?.phone_number?.[0],
      };
      const entries = Object.entries(fieldErrors).filter(
        (entry): entry is [keyof ProfileValues, string] => !!entry[1],
      );
      if (entries.length) {
        entries.forEach(([name, message]) => setError(name, { message }));
      } else {
        toast.error('Nem sikerült menteni az adataidat.', {
          description: getApiErrorMessage(error),
        });
      }
    }
  };

  return (
    <form noValidate onSubmit={(event) => void handleSubmit(onSubmit)(event)}>
      {incomplete && (
        <p className="mb-6 flex gap-3 rounded-2xl border border-warning/30 bg-warning/10 px-4 py-3 text-sm leading-relaxed">
          <TriangleAlertIcon className="mt-0.5 size-4 shrink-0 text-warning" />
          Egészítsd ki az adataidat, hogy felkérést küldhess!
        </p>
      )}
      <FieldGroup>
        <div className="grid gap-5 sm:grid-cols-2">
          <Field data-invalid={!!errors.last_name}>
            <FieldLabel htmlFor="profile-last-name">Vezetéknév</FieldLabel>
            <Input
              aria-invalid={!!errors.last_name}
              autoComplete="family-name"
              id="profile-last-name"
              {...register('last_name')}
            />
            <FieldError errors={[errors.last_name]} />
          </Field>
          <Field data-invalid={!!errors.first_name}>
            <FieldLabel htmlFor="profile-first-name">Keresztnév</FieldLabel>
            <Input
              aria-invalid={!!errors.first_name}
              autoComplete="given-name"
              id="profile-first-name"
              {...register('first_name')}
            />
            <FieldError errors={[errors.first_name]} />
          </Field>
        </div>
        <Field data-invalid={!!errors.email}>
          <FieldLabel htmlFor="profile-email">E-mail-cím</FieldLabel>
          <Input
            aria-invalid={!!errors.email}
            autoComplete="email"
            id="profile-email"
            placeholder="nev@example.com"
            type="email"
            {...register('email')}
          />
          <FieldError errors={[errors.email]} />
        </Field>
        <Field data-invalid={!!errors.phone_number}>
          <FieldLabel htmlFor="profile-phone">Telefonszám</FieldLabel>
          <Input
            aria-invalid={!!errors.phone_number}
            autoComplete="tel"
            id="profile-phone"
            inputMode="tel"
            placeholder="+36 30 123 4567"
            type="tel"
            {...register('phone_number', {
              onBlur: (event: { target: HTMLInputElement }) => {
                const phone = parsePhoneNumberFromString(
                  event.target.value,
                  'HU',
                );
                if (phone?.isValid()) {
                  setValue('phone_number', phone.formatInternational(), {
                    shouldDirty: true,
                  });
                }
              },
            })}
          />
          <FieldDescription>
            Külföldi számnál add meg az országhívót is.
          </FieldDescription>
          <FieldError errors={[errors.phone_number]} />
        </Field>
      </FieldGroup>
      <div className="mt-8 flex justify-end gap-3">
        {isDirty && (
          <Button
            disabled={isSubmitting}
            onClick={() => reset()}
            type="button"
            variant="ghost"
          >
            Mégsem
          </Button>
        )}
        <Button disabled={!isDirty || isSubmitting} type="submit">
          {isSubmitting && (
            <Loader2Icon className="animate-spin" data-icon="inline-start" />
          )}
          Mentés
        </Button>
      </div>
    </form>
  );
}
