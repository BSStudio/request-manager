import React, { cloneElement } from 'react';

import { Calendar } from 'primereact/calendar';
import { classNames } from 'primereact/utils';
import type { IconType } from 'primereact/utils';
import { Controller } from 'react-hook-form';
import type {
  FieldPath,
  FieldValues,
  UseControllerProps,
} from 'react-hook-form';

import ConditionalWrapper from 'admin/helpers/ConditionalWrapper';

interface FormFieldProps<
  T extends FieldValues = FieldValues,
  TName extends FieldPath<T> = FieldPath<T>,
> extends UseControllerProps<T, TName> {
  children: React.JSX.Element;
  className: string;
  icon?: IconType<FormFieldProps<T, TName>>;
  // PrimeReact's Calendar, Dropdown and AutoComplete put id on a wrapper and
  // take their input's id as inputId.
  inputId?: boolean;
  label: string;
}

export const errorMessages: Record<string, string> = {
  maxLength: 'A mező túl hosszú',
  required: 'A mező kitöltése kötelező',
  validate: 'A mező kitöltése kötelező',
};

const FormField = <
  T extends FieldValues = FieldValues,
  TName extends FieldPath<T> = FieldPath<T>,
>({
  className,
  children,
  icon,
  inputId,
  label,
  ...controllerProps
}: FormFieldProps<T, TName>) => {
  return (
    <Controller
      {...controllerProps}
      render={({ field, fieldState }) => {
        const aria = {
          'aria-describedby': fieldState.error && `${field.name}-help`,
          'aria-invalid': fieldState.invalid || undefined,
        };
        return (
          <div className={classNames('field', className)}>
            <label className="font-medium text-900" htmlFor={field.name}>
              {label}
            </label>
            <ConditionalWrapper
              condition={!!icon}
              wrapper={(children) => (
                <div className="p-inputgroup">
                  <span className="p-inputgroup-addon">
                    <i className={`pi ${icon}`} />
                  </span>
                  {children}
                </div>
              )}
            >
              {cloneElement(children, {
                // Calendar keeps ARIA props on its wrapper; its input takes them
                // through pt.
                ...(children.type === Calendar
                  ? { pt: { input: { root: aria } } }
                  : aria),
                className: fieldState.error && 'p-invalid',
                [inputId ? 'inputId' : 'id']: field.name,
                ...field,
              })}
            </ConditionalWrapper>
            {fieldState.error && (
              <small className="block p-error" id={field.name + '-help'}>
                {fieldState.error.message ||
                  errorMessages[fieldState.error.type]}
              </small>
            )}
          </div>
        );
      }}
    />
  );
};

export default FormField;
