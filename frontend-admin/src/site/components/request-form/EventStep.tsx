import { useEffect } from 'react';

import { addDays } from 'date-fns';
import { PencilLineIcon, TriangleAlertIcon } from 'lucide-react';
import {
  Controller,
  useController,
  useFormContext,
  useWatch,
} from 'react-hook-form';

import DateTimeField from 'site/components/request-form/DateTimeField';
import {
  OTHER_TYPE,
  type RequestFormValues,
  toDateTime,
} from 'site/components/request-form/schema';
import TextField from 'site/components/request-form/TextField';
import {
  Field,
  FieldContent,
  FieldError,
  FieldGroup,
  FieldLabel,
  FieldLegend,
  FieldSet,
  FieldTitle,
} from 'site/components/ui/field';
import { RadioGroup, RadioGroupItem } from 'site/components/ui/radio-group';
import { requestTypes } from 'site/lib/requestTypes';

const typeOptions = [
  ...requestTypes.map(({ icon, title }) => ({ icon, title, value: title })),
  { icon: PencilLineIcon, title: 'Egyéb', value: OTHER_TYPE },
];

function DateTimeController({
  label,
  prefix,
}: {
  label: string;
  prefix: 'end' | 'start';
}) {
  const date = useController<RequestFormValues>({ name: `${prefix}Date` });
  const time = useController<RequestFormValues>({ name: `${prefix}Time` });
  const id = `request-${prefix}`;

  return (
    <Field data-invalid={!!(date.fieldState.error || time.fieldState.error)}>
      <FieldLabel htmlFor={id} id={`${id}-label`}>
        {label}
      </FieldLabel>
      <DateTimeField
        date={date.field.value}
        dateInvalid={!!date.fieldState.error}
        dateRef={date.field.ref}
        id={id}
        labelId={`${id}-label`}
        onDateChange={date.field.onChange}
        onTimeChange={time.field.onChange}
        time={time.field.value}
        timeInvalid={!!time.fieldState.error}
        timeRef={time.field.ref}
      />
      <FieldError errors={[date.fieldState.error ?? time.fieldState.error]} />
    </Field>
  );
}

export default function EventStep() {
  const {
    control,
    formState: { errors },
    getValues,
    setValue,
  } = useFormContext<RequestFormValues>();
  const [startDate, startTime, type] = useWatch<
    RequestFormValues,
    ['startDate', 'startTime', 'type']
  >({ name: ['startDate', 'startTime', 'type'] });
  const start = toDateTime(startDate, startTime);
  const soon = start && start < addDays(new Date(), 8);

  // Most events end on the day they start.
  useEffect(() => {
    if (startDate && !getValues('endDate')) setValue('endDate', startDate);
  }, [startDate, getValues, setValue]);

  return (
    <FieldGroup>
      <TextField
        label="Az esemény neve"
        name="title"
        placeholder="pl. Szakmai nap 2026"
      />
      <div className="grid gap-5 md:grid-cols-2">
        <DateTimeController label="Kezdés" prefix="start" />
        <DateTimeController label="Várható befejezés" prefix="end" />
      </div>
      {soon && (
        <div className="flex gap-3 rounded-2xl border border-warning/40 bg-warning/10 p-4 text-sm">
          <TriangleAlertIcon className="mt-0.5 size-4 shrink-0 text-warning" />
          <p>
            Ez kevesebb, mint 8 nap. Lehet, hogy már nem tudjuk elvállalni, de a
            hétfői gyűlésünkön megnézzük.
          </p>
        </div>
      )}
      <TextField
        label="Helyszín"
        name="place"
        placeholder="Az esemény pontos helye"
      />
      <FieldSet data-invalid={!!errors.type}>
        <FieldLegend variant="label">Milyen videót szeretnél?</FieldLegend>
        <Controller
          control={control}
          name="type"
          render={({ field }) => (
            <RadioGroup
              aria-invalid={!!errors.type}
              className="grid gap-3 sm:grid-cols-2"
              onValueChange={field.onChange}
              value={field.value}
            >
              {typeOptions.map(({ icon: Icon, title, value }, index) => (
                <FieldLabel htmlFor={`request-type-${index}`} key={value}>
                  <Field orientation="horizontal">
                    <Icon className="size-5 shrink-0 text-primary" />
                    <FieldContent>
                      <FieldTitle>{title}</FieldTitle>
                    </FieldContent>
                    <RadioGroupItem
                      id={`request-type-${index}`}
                      value={value}
                    />
                  </Field>
                </FieldLabel>
              ))}
            </RadioGroup>
          )}
        />
        <FieldError errors={[errors.type]} />
      </FieldSet>
      {type === OTHER_TYPE && (
        <TextField
          autoFocus
          label="Írd le, milyen videót szeretnél"
          name="typeOther"
          placeholder="pl. Aftermovie a rendezvényről"
        />
      )}
    </FieldGroup>
  );
}
