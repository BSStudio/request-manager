import { Ripple } from 'primereact/ripple';
import type { IconType } from 'primereact/utils';
import { classNames } from 'primereact/utils';
import { Link } from 'react-router';

interface NavigationButtonProps {
  active: boolean;
  icon: IconType<NavigationButtonProps>;
  section: string;
  text: string;
}

const NavigationButton = ({
  active,
  icon,
  section,
  text,
}: NavigationButtonProps) => {
  return (
    <li>
      <Link
        aria-current={active ? 'page' : undefined}
        // Narrow screens show only the icon.
        aria-label={text}
        className={classNames(
          'align-items-center border-round flex hover:surface-hover no-underline p-3 p-ripple transition-colors transition-duration-150',
          active ? 'surface-hover text-primary' : 'text-800',
        )}
        replace
        to={`?section=${section}`}
      >
        <i className={'md:mr-2 ' + icon}></i>
        <span className="font-medium hidden md:block">{text}</span>
        <Ripple />
      </Link>
    </li>
  );
};

export default NavigationButton;
