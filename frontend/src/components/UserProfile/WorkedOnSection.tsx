import { useRef, useState } from 'react';

import { Button } from 'primereact/button';
import { Calendar } from 'primereact/calendar';
import { Column } from 'primereact/column';
import { DataTable } from 'primereact/datatable';
import type { DataTableValueArray } from 'primereact/datatable';
import { Divider } from 'primereact/divider';
import { InputSwitch } from 'primereact/inputswitch';
import { SplitButton } from 'primereact/splitbutton';
import { Controller, useForm } from 'react-hook-form';
import { href } from 'react-router';

import { adminApi } from 'api/http';
import { UserAdminWorkedOn } from 'api/models/user-admin-worked-on';
import LinkButton from 'components/LinkButton/LinkButton';
import { dateTimeToLocaleString } from 'helpers/DateToLocaleStringCoverters';

interface IWorkedOnForm {
  is_responsible: boolean;
  start_datetime_after: Date | null;
  start_datetime_before: Date | null;
}

interface UserAdminWorkedOnDate // TODO: Rename?
  extends Omit<UserAdminWorkedOn, 'start_datetime'> {
  start_datetime: Date;
}

type WorkedOnSectionProps = {
  userId: number;
};

const WorkedOnSection = ({ userId }: WorkedOnSectionProps) => {
  const dataTableRef = useRef<DataTable<DataTableValueArray>>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [workedOnResults, setWorkedOnResults] = useState<
    UserAdminWorkedOnDate[]
  >([]);

  const defaultValues = {
    is_responsible: true,
    start_datetime_after: null,
    start_datetime_before: null,
  };

  const { control, handleSubmit, reset } = useForm<IWorkedOnForm>({
    defaultValues,
  });

  const searchButtonItems = [
    {
      command: () => {
        reset();
        setWorkedOnResults([]);
      },
      icon: 'pi pi-refresh',
      label: 'Visszaállítás',
    },
  ];

  const actionBodyTemplate = ({ id }: UserAdminWorkedOnDate) => {
    return (
      <LinkButton
        buttonProps={{
          'aria-label': 'Ugrás a felkéréshez',
          className: 'p-button-outlined',
          icon: 'pi pi-sign-in',
        }}
        linkProps={{
          to: href('/requests/:requestId', { requestId: id.toString() }),
        }}
      />
    );
  };

  const dateBodyTemplate = ({ start_datetime }: UserAdminWorkedOnDate) => {
    return dateTimeToLocaleString(start_datetime, true);
  };

  const exportCSV = () => {
    if (dataTableRef && dataTableRef.current) {
      dataTableRef.current.exportCSV();
    }
    return null;
  };

  const header = (
    <div className="flex align-items-center justify-content-end gap-2">
      <Button
        icon="pi pi-download"
        onClick={() => exportCSV()}
        rounded
        tooltip="Letöltés CSV fájlként"
        tooltipOptions={{ className: 'text-xs', position: 'left' }}
      />
    </div>
  );

  const onSubmit = async (data: IWorkedOnForm) => {
    setIsLoading(true);
    const start_datetime_after = data.start_datetime_after
      ? data.start_datetime_after.toISOString().split('T')[0]
      : undefined;
    const start_datetime_before = data.start_datetime_before
      ? data.start_datetime_before.toISOString().split('T')[0]
      : undefined;

    await adminApi
      .adminUsersWorkedOnList(
        userId,
        data.is_responsible,
        start_datetime_after,
        start_datetime_before,
      )
      .then((response) => {
        const data = [...response.data].map((request) => {
          return {
            ...request,
            start_datetime: new Date(request.start_datetime),
          };
        });
        setWorkedOnResults(data || []);
      })
      .finally(() => {
        setIsLoading(false);
      });
  };

  return (
    <>
      <div className="font-semibold mt-3 text-900 text-lg">
        Készített anyagok
      </div>
      <Divider />
      <form className="formgrid grid p-fluid">
        <Controller
          control={control}
          name="start_datetime_after"
          render={({ field }) => (
            <div className="field col-12 mb-4 md:col-6">
              <label className="font-medium text-900" htmlFor={field.name}>
                Kezdés időpontja későbbi mint
              </label>
              <Calendar
                {...field}
                mask="9999.99.99"
                placeholder="20 héttel ezelőtt"
                showButtonBar
                showIcon
              />
            </div>
          )}
        />
        <Controller
          control={control}
          name="start_datetime_before"
          render={({ field }) => (
            <div className="field col-12 mb-4 md:col-6">
              <label className="font-medium text-900" htmlFor={field.name}>
                Kezdés időpontja korábbi mint
              </label>
              <Calendar
                {...field}
                mask="9999.99.99"
                placeholder="Ma"
                showButtonBar
                showIcon
              />
            </div>
          )}
        />
        <Controller
          control={control}
          name="is_responsible"
          render={({ field }) => (
            <div className="field col-12 mb-0">
              <div className="align-items-center flex justify-content-between">
                <label className="font-medium text-900" htmlFor={field.name}>
                  Felelős pozíciók
                </label>
                <InputSwitch
                  {...field}
                  checked={!!field.value}
                  inputId={field.name}
                  inputRef={field.ref}
                  onChange={(e) => field.onChange(e.value)}
                  value={undefined}
                />
              </div>
            </div>
          )}
        />
        <Divider />
        <SplitButton
          autoFocus
          className="col-12 lg:col-3"
          icon="pi pi-search"
          label="Keresés"
          loading={isLoading}
          model={searchButtonItems}
          onClick={handleSubmit(onSubmit)}
        />
      </form>
      <Divider />
      <DataTable
        emptyMessage="Nincs találat."
        header={header}
        paginator
        ref={dataTableRef}
        rows={25}
        rowsPerPageOptions={[10, 25, 50, 100]}
        showGridlines
        sortField="start_datetime"
        sortOrder={-1}
        stripedRows
        value={workedOnResults}
      >
        <Column field="title" header="Esemény neve" sortable />
        <Column
          align="center"
          body={dateBodyTemplate}
          dataType="date"
          field="start_datetime"
          header="Kezdés ideje"
          sortable
          style={{ whiteSpace: 'nowrap' }}
        />
        <Column field="position" header="Pozíció" sortable />
        <Column
          body={actionBodyTemplate}
          bodyStyle={{ overflow: 'visible', textAlign: 'center' }}
          headerStyle={{ textAlign: 'center', width: '4rem' }}
        />
      </DataTable>
    </>
  );
};

export default WorkedOnSection;
