import { InfoIcon } from 'lucide-react';
import { toast } from 'sonner';

import { getApiErrorMessage } from 'api/errors';
import { pushDescriptions, pushHints } from 'helpers/push';
import { usePushSubscription } from 'hooks/usePushSubscription';
import DetailCard from 'site/components/DetailCard';
import {
  Field,
  FieldContent,
  FieldDescription,
  FieldLabel,
} from 'site/components/ui/field';
import { Switch } from 'site/components/ui/switch';

export default function PushSwitch() {
  const { available, pending, state, toggle } = usePushSubscription(
    (message, error) =>
      toast.error(message, { description: getApiErrorMessage(error) }),
  );
  if (!available) return null;

  const hint = state && pushHints[state];

  return (
    <DetailCard title="Értesítések">
      <Field orientation="horizontal">
        <FieldContent>
          <FieldLabel htmlFor="push-switch">Push értesítések</FieldLabel>
          <FieldDescription>{pushDescriptions.site}</FieldDescription>
        </FieldContent>
        <Switch
          checked={state === 'on'}
          disabled={pending || (state !== 'on' && state !== 'off')}
          id="push-switch"
          onCheckedChange={toggle}
        />
      </Field>
      {hint && (
        <p className="mt-5 flex gap-3 rounded-2xl bg-muted/50 px-4 py-3 text-sm leading-relaxed">
          <InfoIcon className="mt-0.5 size-4 shrink-0 text-primary" />
          {hint}
        </p>
      )}
    </DetailCard>
  );
}
