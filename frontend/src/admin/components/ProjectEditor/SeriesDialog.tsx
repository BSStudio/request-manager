import { Button } from 'primereact/button';
import { Calendar } from 'primereact/calendar';
import { Dialog } from 'primereact/dialog';
import { SelectButton } from 'primereact/selectbutton';
import { useForm, useWatch } from 'react-hook-form';

import FormField from 'admin/components/FormField/FormField';
import { parseDateTimeInput } from 'admin/helpers/parseDateTimeInput';
import { occurrences } from 'admin/helpers/projectRows';

type SeriesValues = {
  firstEnd: Date | null;
  firstStart: Date | null;
  lastDay: Date | null;
  repeat: 'daily' | 'weekly';
};

type SeriesDialogProps = {
  onAdd: (rows: { end_datetime: Date; start_datetime: Date }[]) => void;
  onHide: () => void;
  visible: boolean;
};

const defaultValues: SeriesValues = {
  firstEnd: null,
  firstStart: null,
  lastDay: null,
  repeat: 'weekly',
};

const repeatOptions = [
  { label: 'Naponta', value: 'daily' },
  { label: 'Hetente', value: 'weekly' },
];

const SeriesDialog = ({ onAdd, onHide, visible }: SeriesDialogProps) => {
  const { control, reset } = useForm<SeriesValues>({ defaultValues });
  const [firstStart, firstEnd, lastDay, repeat] = useWatch({
    control,
    name: ['firstStart', 'firstEnd', 'lastDay', 'repeat'],
  });

  const series =
    firstStart && firstEnd && lastDay && firstEnd > firstStart
      ? occurrences(firstStart, firstEnd, lastDay, repeat)
      : [];

  const close = () => {
    reset(defaultValues);
    onHide();
  };

  const footer = (
    <div>
      <Button label="Mégsem" onClick={close} text type="button" />
      <Button
        disabled={!series.length}
        label="Alkalmak hozzáadása"
        onClick={() => {
          onAdd(
            series.map(({ end, start }) => ({
              end_datetime: end,
              start_datetime: start,
            })),
          );
          close();
        }}
        type="button"
      />
    </div>
  );

  return (
    <Dialog
      breakpoints={{ '768px': '95vw' }}
      footer={footer}
      header="Ismétlődő alkalmak"
      onHide={close}
      style={{ width: '40rem' }}
      visible={visible}
    >
      <div className="formgrid grid p-fluid">
        <FormField
          className="col-12 md:col-6"
          control={control}
          inputId
          label="Első alkalom kezdete"
          name="firstStart"
        >
          <Calendar
            mask="9999.99.99 99:99"
            parseDateTime={parseDateTimeInput}
            showButtonBar
            showIcon
            showOnFocus={false}
            showTime
          />
        </FormField>
        <FormField
          className="col-12 md:col-6"
          control={control}
          inputId
          label="Első alkalom vége"
          name="firstEnd"
        >
          <Calendar
            mask="9999.99.99 99:99"
            parseDateTime={parseDateTimeInput}
            showButtonBar
            showIcon
            showOnFocus={false}
            showTime
          />
        </FormField>
        <FormField
          className="col-12 md:col-6"
          control={control}
          inputId
          label="Utolsó alkalom napja"
          name="lastDay"
        >
          <Calendar mask="9999.99.99" showIcon showOnFocus={false} />
        </FormField>
        <FormField
          className="col-12 md:col-6"
          control={control}
          label="Ismétlés"
          name="repeat"
        >
          <SelectButton allowEmpty={false} options={repeatOptions} />
        </FormField>
        <div className="col-12 text-600">{series.length} alkalom</div>
      </div>
    </Dialog>
  );
};

export default SeriesDialog;
