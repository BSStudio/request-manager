import { forwardRef } from 'react';

import { Button } from 'primereact/button';

type JumpButtonProps = {
  onClick: React.MouseEventHandler<HTMLButtonElement>;
};

const JumpButton = forwardRef<React.Ref<HTMLTableElement>, JumpButtonProps>(
  ({ onClick }, ref) => {
    return (
      <Button
        className="p-button-sm p-button-text px-1 py-0"
        icon="pi pi-angle-right"
        label="Ugrás"
        onClick={onClick}
        {...ref}
      />
    );
  },
);
JumpButton.displayName = 'JumpButton';

export default JumpButton;
