import type { ComponentProps } from 'react';

import { type RegisterOptions, useFormContext } from 'react-hook-form';

import type { RequestFormValues } from 'site/components/request-form/schema';
import {
  Field,
  FieldDescription,
  FieldError,
  FieldLabel,
} from 'site/components/ui/field';
import { Input } from 'site/components/ui/input';

type TextFieldProps = Omit<ComponentProps<'input'>, 'name'> & {
  description?: string;
  label: string;
  name: keyof RequestFormValues;
  registerOptions?: RegisterOptions<RequestFormValues>;
};

export default function TextField({
  description,
  label,
  name,
  registerOptions,
  ...inputProps
}: TextFieldProps) {
  const {
    formState: { errors },
    register,
  } = useFormContext<RequestFormValues>();
  const error = errors[name];
  const id = `request-${name}`;

  return (
    <Field data-invalid={!!error}>
      <FieldLabel htmlFor={id}>{label}</FieldLabel>
      <Input
        aria-invalid={!!error}
        id={id}
        {...inputProps}
        {...register(name, registerOptions)}
      />
      {description && <FieldDescription>{description}</FieldDescription>}
      <FieldError errors={[error]} />
    </Field>
  );
}
