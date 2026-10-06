import { Badge } from 'primereact/badge';
import { Ripple } from 'primereact/ripple';
import type { IconType } from 'primereact/utils';
import { Link } from 'react-router';

type ButtonProps = {
  badgeValue?: string;
  icon: IconType<ButtonProps>;
  label: string;
  path: string;
};

const Button = ({ badgeValue, icon, label, path }: ButtonProps) => {
  return (
    <li>
      <Link
        className="align-items-center border-left-2 border-transparent cursor-pointer flex font-medium h-full hover:border-primary hover:text-900 lg:border-bottom-2 lg:border-left-none lg:px-3 lg:py-2 no-underline p-3 p-ripple px-6 text-600 transition-colors transition-duration-150"
        to={path}
      >
        <i className={`mr-2 pi ${icon}`}></i>
        <span>{label}</span>
        {badgeValue && <Badge className="ml-2" value={badgeValue} />}
        <Ripple />
      </Link>
    </li>
  );
};

export default Button;
