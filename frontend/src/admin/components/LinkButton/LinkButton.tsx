import type { ButtonProps } from 'primereact/button';
import { Ripple } from 'primereact/ripple';
import { classNames } from 'primereact/utils';
import { Link } from 'react-router';
import type { LinkProps } from 'react-router';

interface LinkButtonProps {
  buttonProps: Pick<ButtonProps, 'aria-label' | 'className' | 'label'> & {
    icon?: string;
  };
  linkProps: LinkProps;
}

// One tab stop per control, so a link dressed as PrimeReact's button markup.
export default function LinkButton({
  buttonProps: { 'aria-label': ariaLabel, className, icon, label },
  linkProps: { className: linkClassName, ...linkProps },
}: LinkButtonProps) {
  return (
    <Link
      aria-label={ariaLabel}
      className={classNames(
        'no-underline p-button p-component p-ripple',
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
      {/* An icon-only button keeps an empty label for its line height. */}
      <span className="p-button-label p-c">{label || ' '}</span>
      <Ripple />
    </Link>
  );
}
