import { useRef } from 'react';

import { Ripple } from 'primereact/ripple';
import { StyleClass } from 'primereact/styleclass';
import { href, Link } from 'react-router';

import Avatar from 'admin/components/Avatar/Avatar';
import { showErrorToast } from 'admin/helpers/showErrorToast';
import { signOut, useSessionUser } from 'helpers/session';

const itemClassName =
  'align-items-center border-left-2 border-transparent cursor-pointer flex hover:border-primary hover:text-900 no-underline p-3 p-ripple text-600 transition-colors transition-duration-150';

const AvatarButton = () => {
  const btnRef = useRef(null);
  const user = useSessionUser();

  if (!user) return null;

  const profilePath = href('/users/:userId', { userId: user.id.toString() });

  const close = () => (btnRef.current as HTMLAnchorElement | null)?.click();

  const handleSignOut = async () => {
    try {
      await signOut();
    } catch (error) {
      showErrorToast(error);
      return;
    }
    window.location.href = '/';
  };

  return (
    <li className="border-top-1 lg:border-top-none lg:relative surface-border">
      <StyleClass
        enterActiveClassName="scalein"
        enterFromClassName="hidden"
        hideOnOutsideClick
        leaveActiveClassName="fadeout"
        leaveToClassName="hidden"
        nodeRef={btnRef}
        selector="@next"
      >
        <a
          aria-label="Fiók"
          className="align-items-center border-left-2 border-transparent cursor-pointer flex font-medium h-full hover:border-primary lg:border-bottom-2 lg:border-left-none lg:px-3 lg:py-2 p-3 no-underline p-ripple px-6 transition-colors transition-duration-150"
          ref={btnRef}
        >
          <Avatar
            className="lg:mr-0 mr-3"
            image={user.avatar}
            name={user.name}
          />
          <div className="block lg:hidden">
            <div className="font-medium text-900">{user.name}</div>
            <span className="font-medium text-600 text-sm">
              {user.groups.join(', ')}
            </span>
          </div>
          <i className="lg:ml-2 ml-auto pi pi-angle-down text-600"></i>
          <Ripple />
        </a>
      </StyleClass>

      <ul className="border-50 border-round hidden lg:absolute lg:border-1 lg:px-0 lg:right-0 lg:shadow-2 lg:w-15rem list-none m-0 origin-top px-6 py-0 shadow-0 surface-overlay w-full">
        <li className="border-bottom-1 hidden lg:block p-3 surface-border">
          <div className="font-medium text-900">{user.name}</div>
          <span className="font-medium text-600 text-sm">
            {user.groups.join(', ')}
          </span>
        </li>
        <li>
          <Link className={itemClassName} onClick={close} to={profilePath}>
            <i className="mr-2 pi pi-user"></i>
            <span className="font-medium">Profilom</span>
            <Ripple />
          </Link>
        </li>
        <li>
          <Link
            className={itemClassName}
            onClick={close}
            to={`${profilePath}?section=workedOn`}
          >
            <i className="mr-2 pi pi-list"></i>
            <span className="font-medium">Anyagaim</span>
            <Ripple />
          </Link>
        </li>
        <li>
          <a className={itemClassName} href="/">
            <i className="mr-2 pi pi-globe"></i>
            <span className="font-medium">Vissza a weboldalra</span>
            <Ripple />
          </a>
        </li>
        <li>
          <a className={itemClassName} onClick={() => void handleSignOut()}>
            <i className="mr-2 pi pi-sign-out"></i>
            <span className="font-medium">Kijelentkezés</span>
            <Ripple />
          </a>
        </li>
      </ul>
    </li>
  );
};

export default AvatarButton;
