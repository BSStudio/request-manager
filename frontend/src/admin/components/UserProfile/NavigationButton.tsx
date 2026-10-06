import { Ripple } from 'primereact/ripple';
import type { IconType } from 'primereact/utils';

interface NavigationButtonProps {
  icon: IconType<NavigationButtonProps>;
  onClick: React.MouseEventHandler<HTMLAnchorElement>;
  text: string;
}

const NavigationButton = ({ icon, onClick, text }: NavigationButtonProps) => {
  return (
    <li>
      <a
        className="align-items-center border-round cursor-pointer flex hover:surface-hover p-3 p-ripple text-800 transition-colors transition-duration-150"
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
