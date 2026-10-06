import { Ripple } from 'primereact/ripple';

import Avatar from 'admin/components/Avatar/Avatar';
import { useSessionUser } from 'helpers/session';

const AvatarButton = () => {
  const user = useSessionUser();

  return (
    <li className="border-top-1 lg:border-top-none surface-border">
      <a
        className="align-items-center border-left-2 border-transparent cursor-pointer flex font-medium h-full hover:border-primary lg:border-bottom-2 lg:border-left-none lg:px-3 lg:py-2 p-3 no-underline p-ripple px-6 transition-colors transition-duration-150"
        href="/profile"
      >
        <Avatar
          className="lg:mr-0 mr-3"
          image={user?.avatar}
          name={user?.name}
        />
        <div className="block lg:hidden">
          <div className="font-medium text-900">{user?.name}</div>
          <span className="font-medium text-600 text-sm">
            {user?.groups.join(', ')}
          </span>
        </div>
        <Ripple />
      </a>
    </li>
  );
};

export default AvatarButton;
