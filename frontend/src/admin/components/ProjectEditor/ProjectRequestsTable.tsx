import { Button } from 'primereact/button';
import { Calendar } from 'primereact/calendar';
import { Column } from 'primereact/column';
import { DataTable } from 'primereact/datatable';
import { Dropdown } from 'primereact/dropdown';
import { InputText } from 'primereact/inputtext';
import { Tag } from 'primereact/tag';
import { classNames } from 'primereact/utils';
import { Controller } from 'react-hook-form';
import type { Control, FieldArrayWithId } from 'react-hook-form';

import LinkButton from 'admin/components/LinkButton/LinkButton';
import { RequestStatusTag } from 'admin/components/StatusTag/StatusTag';
import { dateTimeToLocaleString } from 'admin/helpers/DateToLocaleStringCoverters';
import { parseDateTimeInput } from 'admin/helpers/parseDateTimeInput';
import { requestTypeOptions } from 'admin/helpers/requestTypes';
import type {
  ExistingRow,
  IProjectEditor,
} from 'admin/pages/ProjectCreatorEditorPage';

type TableRow =
  | { key: string; kind: 'existing'; row: ExistingRow }
  | { index: number; key: string; kind: 'new' };

type ProjectRequestsTableProps = {
  control: Control<IProjectEditor>;
  disabled: boolean;
  existing: ExistingRow[];
  newRows: FieldArrayWithId<IProjectEditor, 'new_requests'>[];
  onDropNew: (index: number) => void;
  onToggleExisting: (requestId: number) => void;
  placeholders: { place: string; title: string; type: string };
};

function cellLabel(column: string, index: number) {
  return `${column}, ${index + 1}. új felkérés`;
}

function startTime({ request }: ExistingRow) {
  return new Date(request.start_datetime).getTime();
}

const ProjectRequestsTable = ({
  control,
  disabled,
  existing,
  newRows,
  onDropNew,
  onToggleExisting,
  placeholders,
}: ProjectRequestsTableProps) => {
  const rows: TableRow[] = [
    ...[...existing]
      .sort((a, b) => startTime(a) - startTime(b))
      .map((row) => ({
        key: `request-${row.request.id}`,
        kind: 'existing' as const,
        row,
      })),
    ...newRows.map((field, index) => ({
      index,
      key: field.id,
      kind: 'new' as const,
    })),
  ];

  const textCell = (
    tableRow: TableRow,
    name: 'place' | 'title',
    column: string,
    placeholder: string,
  ) => {
    if (tableRow.kind === 'existing') return tableRow.row.request[name];
    return (
      <Controller
        control={control}
        disabled={disabled}
        name={`new_requests.${tableRow.index}.${name}`}
        render={({ field, fieldState }) => (
          <>
            <InputText
              {...field}
              aria-invalid={fieldState.invalid || undefined}
              aria-label={cellLabel(column, tableRow.index)}
              className={classNames('w-full', {
                'border-dashed': !field.value,
                'p-invalid': fieldState.invalid,
              })}
              placeholder={placeholder}
            />
            {fieldState.error && (
              <small className="p-error">{fieldState.error.message}</small>
            )}
          </>
        )}
      />
    );
  };

  const timeCell = (
    tableRow: TableRow,
    name: 'end_datetime' | 'start_datetime',
    column: string,
  ) => {
    if (tableRow.kind === 'existing') {
      return dateTimeToLocaleString(new Date(tableRow.row.request[name]), true);
    }
    return (
      <Controller
        control={control}
        disabled={disabled}
        name={`new_requests.${tableRow.index}.${name}`}
        render={({ field, fieldState }) => (
          <>
            <Calendar
              {...field}
              className={classNames('w-full', {
                'p-invalid': fieldState.invalid,
              })}
              mask="9999.99.99 99:99"
              parseDateTime={parseDateTimeInput}
              pt={{
                input: {
                  root: {
                    'aria-invalid': fieldState.invalid || undefined,
                    'aria-label': cellLabel(column, tableRow.index),
                  },
                },
              }}
              showButtonBar
              showIcon
              showOnFocus={false}
              showTime
            />
            {fieldState.error && (
              <small className="p-error">{fieldState.error.message}</small>
            )}
          </>
        )}
      />
    );
  };

  const typeCell = (tableRow: TableRow) => {
    if (tableRow.kind === 'existing') return tableRow.row.request.type;
    return (
      <Controller
        control={control}
        disabled={disabled}
        name={`new_requests.${tableRow.index}.type`}
        render={({ field, fieldState }) => (
          <>
            <Dropdown
              {...field}
              aria-label={cellLabel('Videó típusa', tableRow.index)}
              className={classNames('w-full', {
                'border-dashed': !field.value,
                'p-invalid': fieldState.invalid,
              })}
              editable
              options={requestTypeOptions}
              placeholder={placeholders.type}
            />
            {fieldState.error && (
              <small className="p-error">{fieldState.error.message}</small>
            )}
          </>
        )}
      />
    );
  };

  const statusCell = (tableRow: TableRow) => {
    if (tableRow.kind === 'new') return <Tag value="Új" />;
    const { request, state } = tableRow.row;
    return (
      <div className="align-items-center flex flex-wrap gap-2">
        <RequestStatusTag
          modified={request.status_by_admin}
          statusNum={request.status}
        />
        {state === 'added' && <Tag severity="info" value="Hozzáadva" />}
      </div>
    );
  };

  const actionCell = (tableRow: TableRow) => {
    if (tableRow.kind === 'new') {
      return (
        <Button
          aria-label="Sor törlése"
          disabled={disabled}
          icon="pi pi-trash"
          onClick={() => onDropNew(tableRow.index)}
          rounded
          severity="danger"
          text
          type="button"
        />
      );
    }
    const { request, state } = tableRow.row;
    return (
      <div className="flex gap-1 justify-content-center">
        <LinkButton
          buttonProps={{
            'aria-label': 'Ugrás a felkéréshez',
            className: 'p-button-outlined',
            icon: 'pi pi-external-link',
          }}
          linkProps={{
            rel: 'noopener',
            target: '_blank',
            to: `/requests/${request.id}`,
          }}
        />
        <Button
          aria-label={
            state === 'removed' ? 'Visszavonás' : 'Eltávolítás a projektből'
          }
          disabled={disabled}
          icon={state === 'removed' ? 'pi pi-undo' : 'pi pi-times'}
          onClick={() => onToggleExisting(request.id)}
          rounded
          severity={state === 'removed' ? 'secondary' : 'danger'}
          text
          type="button"
        />
      </div>
    );
  };

  return (
    <DataTable
      dataKey="key"
      emptyMessage="Nem található felkérés."
      rowClassName={(tableRow: TableRow) => ({
        'line-through opacity-60':
          tableRow.kind === 'existing' && tableRow.row.state === 'removed',
      })}
      scrollable
      showGridlines
      value={rows}
    >
      <Column
        body={(tableRow: TableRow) =>
          textCell(tableRow, 'title', 'Esemény neve', placeholders.title)
        }
        header="Esemény neve"
        style={{ minWidth: '12rem' }}
      />
      <Column
        body={(tableRow: TableRow) =>
          timeCell(tableRow, 'start_datetime', 'Kezdés')
        }
        header="Kezdés"
        style={{ minWidth: '14rem' }}
      />
      <Column
        body={(tableRow: TableRow) =>
          timeCell(tableRow, 'end_datetime', 'Befejezés')
        }
        header="Befejezés"
        style={{ minWidth: '14rem' }}
      />
      <Column
        body={typeCell}
        header="Videó típusa"
        style={{ minWidth: '12rem' }}
      />
      <Column
        body={(tableRow: TableRow) =>
          textCell(tableRow, 'place', 'Helyszín', placeholders.place)
        }
        header="Helyszín"
        style={{ minWidth: '11rem' }}
      />
      <Column body={statusCell} header="Állapot" />
      <Column body={actionCell} style={{ width: '7rem' }} />
    </DataTable>
  );
};

export default ProjectRequestsTable;
