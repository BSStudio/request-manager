import { parsePhoneNumberFromString } from 'libphonenumber-js';
import { LogInIcon } from 'lucide-react';
import { useFormContext } from 'react-hook-form';
import { Link } from 'react-router';

import type { RequestFormValues } from 'site/components/request-form/schema';
import TextField from 'site/components/request-form/TextField';
import { Button } from 'site/components/ui/button';
import { FieldGroup } from 'site/components/ui/field';

export default function PersonalStep() {
  const { setValue } = useFormContext<RequestFormValues>();

  return (
    <FieldGroup>
      <div className="flex flex-col gap-4 rounded-2xl border border-primary/20 bg-primary/5 p-4 sm:flex-row sm:items-center">
        <p className="flex-1 text-sm">
          <span className="font-medium">Van fiókod?</span> Jelentkezz be, és nem
          kell kitöltened az adataidat, ráadásul követheted a felkérésed
          állapotát is.
        </p>
        <Button asChild className="shrink-0" variant="outline">
          <Link state={{ from: '/new-request' }} to="/login">
            <LogInIcon data-icon="inline-start" />
            Bejelentkezés
          </Link>
        </Button>
      </div>
      <div className="grid gap-5 sm:grid-cols-2">
        <TextField
          autoComplete="family-name"
          label="Vezetéknév"
          name="requesterLastName"
        />
        <TextField
          autoComplete="given-name"
          label="Keresztnév"
          name="requesterFirstName"
        />
      </div>
      <TextField
        autoComplete="email"
        label="E-mail-cím"
        name="requesterEmail"
        placeholder="nev@example.com"
        type="email"
      />
      <TextField
        autoComplete="tel"
        description="Külföldi számnál add meg az országhívót is."
        inputMode="tel"
        label="Telefonszám"
        name="requesterMobile"
        placeholder="+36 30 123 4567"
        registerOptions={{
          onBlur: (event: { target: HTMLInputElement }) => {
            const phone = parsePhoneNumberFromString(event.target.value, 'HU');
            if (phone?.isValid()) {
              setValue('requesterMobile', phone.formatInternational());
            }
          },
        }}
        type="tel"
      />
    </FieldGroup>
  );
}
