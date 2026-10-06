import { forwardRef, useEffect } from 'react';

import { Button } from 'primereact/button';
import { Dialog } from 'primereact/dialog';
import type { DialogProps } from 'primereact/dialog';
import { InputTextarea } from 'primereact/inputtextarea';
import { Controller, useForm } from 'react-hook-form';

import { RequestAdditionalDataType } from 'types/additionalDataTypes';

interface AdditionalDataDialogProps extends DialogProps {
  data: RequestAdditionalDataType;
  error?: string;
  loading: boolean;
  onSave(data: { additional_data: string }): void;
}

const AdditionalDataDialog = forwardRef<
  React.Ref<HTMLDivElement>,
  AdditionalDataDialogProps
>(({ data, error, loading, onHide, onSave, visible, ...props }, ref) => {
  const {
    control,
    formState: { isDirty },
    handleSubmit,
    reset,
    setError,
  } = useForm<{
    additional_data: string;
  }>();

  useEffect(() => {
    const defaultValues = {
      additional_data: JSON.stringify(data, null, 2),
    };
    reset({ ...defaultValues });
  }, [data, reset, visible]);

  useEffect(() => {
    setError('additional_data', { message: error, type: 'backend' });
  }, [error, setError]);

  const renderFooter = () => {
    return (
      <div>
        <Button
          className="p-button-text p-button-secondary"
          disabled={!isDirty || loading}
          icon="pi pi-refresh"
          label="Visszaállítás"
          onClick={() => {
            reset();
          }}
        />
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
      breakpoints={{ '768px': '95vw' }}
      footer={renderFooter}
      header="További adatok szerkesztése"
      onHide={onHide}
      style={{ width: '50vw' }}
      visible={visible}
      {...props}
      {...ref}
    >
      <Controller
        control={control}
        disabled={loading}
        name="additional_data"
        render={({ field, fieldState }) => (
          <>
            <InputTextarea
              {...field}
              autoResize
              className="w-full"
              id={field.name}
              rows={4}
            />
            {fieldState.error && (
              <small className="block p-error" id={field.name + '-help'}>
                {fieldState.error.message}
              </small>
            )}
          </>
        )}
      />
    </Dialog>
  );
});

AdditionalDataDialog.displayName = 'AdditionalDataDialog';
export default AdditionalDataDialog;
