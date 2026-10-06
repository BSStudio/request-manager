import { forwardRef, Fragment } from 'react';

import { AvatarGroup } from 'primereact/avatargroup';
import type { AvatarGroupProps } from 'primereact/avatargroup';
import { Tooltip } from 'primereact/tooltip';
import { classNames } from 'primereact/utils';

import Avatar from 'admin/components/Avatar/Avatar';

interface AvatarGroupCrewProps extends AvatarGroupProps {
  crew?: {
    avatar_url: string | null;
    full_name: string;
  }[];
}

const AvatarGroupCrew = forwardRef<
  React.DetailedHTMLProps<React.HTMLAttributes<HTMLDivElement>, HTMLDivElement>,
  AvatarGroupCrewProps
>(({ crew, ...props }, ref) => {
  const uniqueCrewMembers = [
    ...new Map(crew?.map((item) => [item['full_name'], item])).values(),
  ];

  const crewSize = uniqueCrewMembers.length;
  const additionalCrewMemberNames =
    uniqueCrewMembers
      .slice(4, 10)
      .map((item) => item.full_name)
      .join('\n') +
    (crewSize > 10 ? `\nés további ${crewSize - 10} ember...` : '');

  if (!uniqueCrewMembers.length) return;

  return (
    <AvatarGroup {...ref} {...props}>
      {uniqueCrewMembers.slice(0, 4).map((item, index) => (
        <Fragment key={encodeURIComponent(item.full_name) + '-fragment'}>
          <Tooltip
            className="text-xs"
            position="top"
            target={'.avatarTooltip' + index}
          />
          <Avatar
            className={'avatarTooltip' + index}
            data-pr-tooltip={item.full_name}
            image={item.avatar_url || undefined}
            name={item.full_name}
          />
        </Fragment>
      ))}
      {crewSize >= 5 && (
        <Fragment>
          <Tooltip
            className="text-xs"
            position="top"
            target=".additional-crew-members-avatar"
          />
          <Avatar
            className={classNames(
              'additional-crew-members-avatar',
              crewSize - 4 >= 10 ? 'text-xs' : 'text-sm',
            )}
            data-pr-tooltip={additionalCrewMemberNames}
            label={'+' + (crewSize - 4).toString()}
          />
        </Fragment>
      )}
    </AvatarGroup>
  );
});

AvatarGroupCrew.displayName = 'AvatarGroupCrew';

export default AvatarGroupCrew;
