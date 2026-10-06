import { forwardRef, Fragment } from 'react';

import { Avatar } from 'primereact/avatar';
import { AvatarGroup } from 'primereact/avatargroup';
import type { AvatarGroupProps } from 'primereact/avatargroup';
import { Tooltip } from 'primereact/tooltip';
import { classNames } from 'primereact/utils';

import { UI_AVATAR_URL } from 'localConstants';

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
            icon="pi pi-user"
            image={item.avatar_url || UI_AVATAR_URL + item.full_name}
            shape="circle"
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
            shape="circle"
          />
        </Fragment>
      )}
    </AvatarGroup>
  );
});

AvatarGroupCrew.displayName = 'AvatarGroupCrew';

export default AvatarGroupCrew;
