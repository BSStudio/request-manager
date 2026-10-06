import { forwardRef } from 'react';

import { Avatar as PrimeAvatar } from 'primereact/avatar';
import type { AvatarProps as PrimeAvatarProps } from 'primereact/avatar';
import { classNames } from 'primereact/utils';

import stylesModule from './Avatar.module.css';

const Avatar = forwardRef<React.Ref<HTMLDivElement>, PrimeAvatarProps>(
  ({ className, ...props }, ref) => {
    return (
      <PrimeAvatar
        icon="pi pi-user"
        shape="circle"
        {...props}
        {...ref}
        className={classNames(stylesModule.avatarIcon, className)}
      />
    );
  },
);

Avatar.displayName = 'Avatar';

export default Avatar;
