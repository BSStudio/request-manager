import { InputText } from 'primereact/inputtext';
import type { Control, Path } from 'react-hook-form';

import FormField from 'admin/components/FormField/FormField';
import type { RequesterValues } from 'admin/helpers/requester';

type NewRequesterFormProps<T extends RequesterValues> = {
  control: Control<T>;
  disabled: boolean;
};

const NewRequesterForm = <T extends RequesterValues>({
  control,
  disabled,
}: NewRequesterFormProps<T>) => {
  return (
    <>
      <FormField
        className="col-12 mb-4 md:col-6 mt-4"
        control={control}
        disabled={disabled}
        label="Vezetéknév"
        name={'requester_last_name' as Path<T>}
      >
        <InputText type="text" />
      </FormField>
      <FormField
        className="col-12 mb-4 md:col-6 md:mt-4"
        control={control}
        disabled={disabled}
        label="Keresztnév"
        name={'requester_first_name' as Path<T>}
      >
        <InputText type="text" />
      </FormField>
      <FormField
        className="col-12 mb-4 md:col-6 md:mb-0"
        control={control}
        disabled={disabled}
        icon="pi-envelope"
        label="E-mail cím"
        name={'requester_email' as Path<T>}
      >
        <InputText type="email" />
      </FormField>
      <FormField
        className="col-12 mb-0 md:col-6"
        control={control}
        disabled={disabled}
        icon="pi-phone"
        label="Telefonszám"
        name={'requester_mobile' as Path<T>}
      >
        <InputText type="tel" />
      </FormField>
    </>
  );
};

export default NewRequesterForm;
