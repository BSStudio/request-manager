import { forwardRef } from 'react';

import { Avatar as PrimeAvatar } from 'primereact/avatar';
import type { AvatarProps as PrimeAvatarProps } from 'primereact/avatar';
import { classNames } from 'primereact/utils';

import { getAvatarStyle, getInitials } from 'helpers/avatar';

import stylesModule from './Avatar.module.css';

interface AvatarProps extends PrimeAvatarProps {
  // Colored initials, shown without a picture or when it fails to load.
  name?: string;
}

const Avatar = forwardRef<React.Ref<HTMLDivElement>, AvatarProps>(
  ({ className, name, style, ...props }, ref) => {
    return (
      <PrimeAvatar
        icon="pi pi-user"
        label={name ? getInitials(name) : undefined}
        shape="circle"
        {...props}
        {...ref}
        className={classNames(stylesModule.avatarIcon, className)}
        style={name ? { ...getAvatarStyle(name), ...style } : style}
      />
    );
  },
);

Avatar.displayName = 'Avatar';

export default Avatar;
