import { forwardRef, useEffect } from 'react';

import { Button } from 'primereact/button';
import { Calendar } from 'primereact/calendar';
import { Dialog } from 'primereact/dialog';
import type { DialogProps } from 'primereact/dialog';
import { Controller, useForm } from 'react-hook-form';

interface AcceptRejectDialogProps extends DialogProps {
  loading: boolean;
  onSave(data: { airedDate: Date }): void;
}

const AiredAddDialog = forwardRef<
  React.Ref<HTMLDivElement>,
  AcceptRejectDialogProps
>(({ loading, onHide, onSave, visible, ...props }, ref) => {
  const { control, handleSubmit, reset } = useForm<{
    airedDate: Date;
  }>();

  useEffect(() => {
    reset();
  }, [reset, visible]);

  const renderFooter = () => {
    return (
      <div>
        <Button
          className="p-button-text"
          disabled={loading}
          icon="pi pi-times"
          label="Mégsem"
          onClick={onHide}
        />
        <Button
          autoFocus
          icon="pi pi-check"
          label="Mentés"
          loading={loading}
          onClick={handleSubmit(onSave)}
        />
      </div>
    );
  };

  return (
    <Dialog
      contentClassName="align-item-center flex flex-column justify-content-center"
      breakpoints={{ '768px': '95vw' }}
      footer={renderFooter}
      header="Adásba kerülés hozzáadása"
      onHide={onHide}
      style={{ width: '50vw' }}
      visible={visible}
      {...props}
      {...ref}
    >
      <Controller
        name="airedDate"
        control={control}
        render={({ field }) => (
          <Calendar {...field} inline inputId={field.name} />
        )}
      />
    </Dialog>
  );
});

AiredAddDialog.displayName = 'AiredAddDialog';
export default AiredAddDialog;
