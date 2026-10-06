import { Ripple } from 'primereact/ripple';

import Avatar from 'components/Avatar/Avatar';
import { getAvatar, getGroups, getName } from 'helpers/LocalStorageHelper';

const AvatarButton = () => {
  return (
    <li className="border-top-1 lg:border-top-none surface-border">
      <a
        className="align-items-center border-left-2 border-transparent cursor-pointer flex font-medium h-full hover:border-primary lg:border-bottom-2 lg:border-left-none lg:px-3 lg:py-2 p-3 no-underline p-ripple px-6 transition-colors transition-duration-150"
        href="/profile"
      >
        <Avatar className="lg:mr-0 mr-3" image={getAvatar()} />
        <div className="block lg:hidden">
          <div className="font-medium text-900">{getName()}</div>
          <span className="font-medium text-600 text-sm">
            {getGroups().join(', ')}
          </span>
        </div>
        <Ripple />
      </a>
    </li>
  );
};

export default AvatarButton;
