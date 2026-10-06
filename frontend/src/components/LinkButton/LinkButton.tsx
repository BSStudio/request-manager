import { forwardRef } from 'react';

import { Button } from 'primereact/button';
import type { ButtonProps } from 'primereact/button';
import { classNames } from 'primereact/utils';
import { Link } from 'react-router';
import type { LinkProps } from 'react-router';

interface LinkButtonProps {
  buttonProps: ButtonProps;
  linkProps: LinkProps;
}

const LinkButton = forwardRef<React.Ref<HTMLTableElement>, LinkButtonProps>(
  ({ buttonProps, linkProps }, ref) => {
    const { className, ..._linkProps } = linkProps;
    return (
      <Link className={classNames('no-underline', className)} {..._linkProps}>
        <Button {...buttonProps} {...ref} />
      </Link>
    );
  },
);
LinkButton.displayName = 'LinkButton';

export default LinkButton;
