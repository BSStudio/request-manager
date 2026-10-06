import { Badge } from 'primereact/badge';
import type { BadgeProps } from 'primereact/badge';
import { Ripple } from 'primereact/ripple';
import type { IconType } from 'primereact/utils';
import { useNavigate } from 'react-router';

interface IconButtonWithClickHandler {
  badgeSeverity?: BadgeProps['severity'];
  icon: IconType<IconButtonProps>;
  label: string;
  onClick: React.MouseEventHandler<HTMLAnchorElement>;
  path?: never;
}

interface IconButtonWithPath {
  badgeSeverity?: BadgeProps['severity'];
  icon: IconType<IconButtonProps>;
  label: string;
  onClick?: never;
  path: string;
}

type IconButtonProps = IconButtonWithClickHandler | IconButtonWithPath;

const IconButton = ({
  badgeSeverity,
  icon,
  label,
  onClick,
  path,
}: IconButtonProps) => {
  const navigate = useNavigate();

  const handleClick = (event: React.MouseEvent<HTMLAnchorElement>) => {
    event.preventDefault();
    if (path) void navigate(path);
    if (onClick) onClick(event);
  };

  return (
    <li>
      <a
        className="align-items-center border-left-2 border-transparent cursor-pointer flex font-medium h-full hover:border-primary hover:text-900 lg:border-bottom-2 lg:border-left-none lg:px-3 lg:py-2 p-3 p-ripple px-6 text-600 transition-colors transition-duration-150"
        onClick={(event) => {
          handleClick(event);
        }}
      >
        <i
          className={`lg:mr-0 lg:text-2xl mr-2 p-overlay-badge pi ${icon} text-base`}
        >
          {badgeSeverity && <Badge severity={badgeSeverity} />}
        </i>
        <span className="block font-medium lg:hidden">{label}</span>
        <Ripple />
      </a>
    </li>
  );
};

export default IconButton;
