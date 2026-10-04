import type { ReactNode } from 'react';

import { parsePhoneNumberFromString } from 'libphonenumber-js';
import { PencilIcon } from 'lucide-react';
import { useFormContext } from 'react-hook-form';
import { Link } from 'react-router';

import {
  OTHER_TYPE,
  type RequestFormValues,
  toDateTime,
} from 'site/components/request-form/schema';
import { Button } from 'site/components/ui/button';
import { formatRange } from 'site/lib/dates';

export type Requester = { email: string; name: string; phone: string };

function SummaryCard({
  action,
  children,
  title,
}: {
  action: ReactNode;
  children: ReactNode;
  title: string;
}) {
  return (
    <section className="rounded-2xl border p-5">
      <div className="flex items-center justify-between gap-4">
        <h3 className="font-mono text-xs tracking-[0.2em] text-muted-foreground uppercase">
          {title}
        </h3>
        {action}
      </div>
      <div className="mt-3">{children}</div>
    </section>
  );
}

function EditButton({ onClick }: { onClick: () => void }) {
  return (
    <Button onClick={onClick} size="sm" variant="ghost">
      <PencilIcon data-icon="inline-start" />
      Módosítás
    </Button>
  );
}

type SummaryStepProps = {
  children: ReactNode;
  onEdit: (step: 'event' | 'notes' | 'personal') => void;
  requester: Requester | null;
};

export default function SummaryStep({
  children,
  onEdit,
  requester,
}: SummaryStepProps) {
  const { getValues } = useFormContext<RequestFormValues>();
  const values = getValues();
  const start = toDateTime(values.startDate, values.startTime);
  const end = toDateTime(values.endDate, values.endTime);
  const type = values.type === OTHER_TYPE ? values.typeOther : values.type;
  const contact = requester ?? {
    email: values.requesterEmail,
    name: `${values.requesterLastName} ${values.requesterFirstName}`,
    phone:
      parsePhoneNumberFromString(
        values.requesterMobile,
        'HU',
      )?.formatInternational() ?? values.requesterMobile,
  };

  return (
    <div className="space-y-4">
      <SummaryCard
        action={<EditButton onClick={() => onEdit('event')} />}
        title="Az esemény"
      >
        <p className="text-xl font-semibold">{values.title}</p>
        <dl className="mt-3 grid gap-x-6 gap-y-2 text-sm sm:grid-cols-[auto_1fr]">
          <dt className="text-muted-foreground">Időpont</dt>
          <dd>{start && end && formatRange(start, end)}</dd>
          <dt className="text-muted-foreground">Helyszín</dt>
          <dd>{values.place}</dd>
          <dt className="text-muted-foreground">Videó típusa</dt>
          <dd>{type}</dd>
        </dl>
      </SummaryCard>
      <SummaryCard
        action={
          requester ? (
            <Button asChild size="sm" variant="ghost">
              <Link to="/profile">
                <PencilIcon data-icon="inline-start" />
                Profilom
              </Link>
            </Button>
          ) : (
            <EditButton onClick={() => onEdit('personal')} />
          )
        }
        title="Felkérő"
      >
        <p className="font-medium">{contact.name}</p>
        <p className="mt-1 text-sm text-muted-foreground">
          {contact.email} · {contact.phone}
        </p>
      </SummaryCard>
      {values.comment.trim() && (
        <SummaryCard
          action={<EditButton onClick={() => onEdit('notes')} />}
          title="Megjegyzés"
        >
          <p className="text-sm whitespace-pre-wrap">{values.comment}</p>
        </SummaryCard>
      )}
      {children}
    </div>
  );
}
