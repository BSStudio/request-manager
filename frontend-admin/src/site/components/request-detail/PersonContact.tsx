import { MailIcon, PhoneIcon } from 'lucide-react';

import type { UserNestedDetail } from 'api/models';
import { Avatar, AvatarFallback, AvatarImage } from 'site/components/ui/avatar';
import { formatPhone } from 'site/lib/person';
import { getInitials } from 'site/lib/session';

const linkClass =
  'flex min-w-0 items-center gap-2 text-sm text-muted-foreground transition-colors hover:text-foreground';

export default function PersonContact({
  person,
}: {
  person: UserNestedDetail;
}) {
  const phone = person.phone_number ? formatPhone(person.phone_number) : null;

  return (
    <div className="flex gap-3">
      <Avatar size="lg">
        <AvatarImage alt="" src={person.avatar_url || undefined} />
        <AvatarFallback className="bg-primary text-xs font-semibold text-primary-foreground">
          {getInitials(person.full_name)}
        </AvatarFallback>
      </Avatar>
      <div className="min-w-0 space-y-1">
        <p className="font-medium">{person.full_name}</p>
        {person.email && (
          <a className={linkClass} href={`mailto:${person.email}`}>
            <MailIcon className="size-4 shrink-0" />
            <span className="truncate">{person.email}</span>
          </a>
        )}
        {phone && (
          <a className={linkClass} href={`tel:${person.phone_number}`}>
            <PhoneIcon className="size-4 shrink-0" />
            {phone}
          </a>
        )}
      </div>
    </div>
  );
}
