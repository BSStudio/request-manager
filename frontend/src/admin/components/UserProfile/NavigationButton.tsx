import { Ripple } from 'primereact/ripple';
import type { IconType } from 'primereact/utils';
import { classNames } from 'primereact/utils';

interface NavigationButtonProps {
  active: boolean;
  icon: IconType<NavigationButtonProps>;
  onClick: React.MouseEventHandler<HTMLAnchorElement>;
  text: string;
}

const NavigationButton = ({
  active,
  icon,
  onClick,
  text,
}: NavigationButtonProps) => {
  return (
    <li>
      <a
        aria-current={active ? 'page' : undefined}
        className={classNames(
          'align-items-center border-round cursor-pointer flex hover:surface-hover p-3 p-ripple transition-colors transition-duration-150',
          active ? 'surface-hover text-primary' : 'text-800',
        )}
        onClick={onClick}
      >
        <i className={'md:mr-2 ' + icon}></i>
        <span className="font-medium hidden md:block">{text}</span>
        <Ripple />
      </a>
    </li>
  );
};

export default NavigationButton;
