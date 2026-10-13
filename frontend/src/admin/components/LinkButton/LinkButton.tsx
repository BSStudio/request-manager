import type { ButtonProps } from 'primereact/button';
import { classNames } from 'primereact/utils';
import { Link } from 'react-router';
import type { LinkProps } from 'react-router';

interface LinkButtonProps {
  buttonProps: Pick<ButtonProps, 'aria-label' | 'className' | 'label'> & {
    icon?: string;
  };
  linkProps: LinkProps;
}

// A link styled as PrimeReact's button rather than a button inside a link,
// which would be two tab stops for one control.
export default function LinkButton({
  buttonProps: { 'aria-label': ariaLabel, className, icon, label },
  linkProps: { className: linkClassName, ...linkProps },
}: LinkButtonProps) {
  return (
    <Link
      aria-label={ariaLabel}
      className={classNames(
        'no-underline p-button p-component',
        !label && 'p-button-icon-only',
        className,
        linkClassName,
      )}
      {...linkProps}
    >
      {icon && (
        <span
          className={classNames(
            'p-button-icon p-c',
            label && 'p-button-icon-left',
            icon,
          )}
        />
      )}
      {label && <span className="p-button-label p-c">{label}</span>}
    </Link>
  );
}
