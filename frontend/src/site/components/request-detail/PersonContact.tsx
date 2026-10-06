import { MailIcon, PhoneIcon } from 'lucide-react';

import type { UserNestedDetail } from 'api/models';
import UserAvatar from 'site/components/UserAvatar';
import { formatPhone } from 'site/lib/person';

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
      <UserAvatar
        size="lg"
        user={{ avatar: person.avatar_url, name: person.full_name }}
      />
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
