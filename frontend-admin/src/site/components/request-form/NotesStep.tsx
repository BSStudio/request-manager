import { useFormContext } from 'react-hook-form';

import type { RequestFormValues } from 'site/components/request-form/schema';
import { Field, FieldDescription, FieldLabel } from 'site/components/ui/field';
import { Textarea } from 'site/components/ui/textarea';

export default function NotesStep() {
  const { register } = useFormContext<RequestFormValues>();

  return (
    <Field>
      <FieldLabel htmlFor="request-comment">Megjegyzés</FieldLabel>
      <Textarea
        className="min-h-56"
        id="request-comment"
        placeholder="Az esemény menetrendje időpontokkal, különleges kérések, a pontos helyszín…"
        {...register('comment')}
      />
      <FieldDescription>
        Nem kötelező, de sokat segít a tervezésben.
      </FieldDescription>
    </Field>
  );
}
