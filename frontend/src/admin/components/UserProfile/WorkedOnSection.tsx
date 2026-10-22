import { useRef, useState } from 'react';

import { format, parseISO } from 'date-fns';
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

import LinkButton from 'admin/components/LinkButton/LinkButton';
import { dateToLocaleString } from 'admin/helpers/DateToLocaleStringCoverters';
import { showErrorToast } from 'admin/helpers/showErrorToast';
import { adminApi } from 'api/http';
import { UserAdminWorkedOn } from 'api/models/user-admin-worked-on';

interface IWorkedOnForm {
  date_after: Date | null;
  date_before: Date | null;
  is_responsible: boolean;
}

type WorkedOnSectionProps = {
  userId: number;
};

const WorkedOnSection = ({ userId }: WorkedOnSectionProps) => {
  const dataTableRef = useRef<DataTable<DataTableValueArray>>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [workedOnResults, setWorkedOnResults] = useState<UserAdminWorkedOn[]>(
    [],
  );

  const defaultValues = {
    date_after: null,
    date_before: null,
    is_responsible: true,
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

  const actionBodyTemplate = ({ id }: UserAdminWorkedOn) => {
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

  const dateBodyTemplate = ({ date }: UserAdminWorkedOn) => {
    return dateToLocaleString(parseISO(date), true);
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
    const date_after = data.date_after
      ? format(data.date_after, 'yyyy-MM-dd')
      : undefined;
    const date_before = data.date_before
      ? format(data.date_before, 'yyyy-MM-dd')
      : undefined;

    await adminApi
      .adminUsersWorkedOnList({
        dateAfter: date_after,
        dateBefore: date_before,
        id: userId,
        isResponsible: data.is_responsible,
      })
      .then((response) => {
        setWorkedOnResults(response.data);
      })
      .catch(showErrorToast)
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
          name="date_after"
          render={({ field }) => (
            <div className="field col-12 mb-4 md:col-6">
              <label className="font-medium text-900" htmlFor={field.name}>
                Időszak kezdete
              </label>
              <Calendar
                {...field}
                inputId={field.name}
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
          name="date_before"
          render={({ field }) => (
            <div className="field col-12 mb-4 md:col-6">
              <label className="font-medium text-900" htmlFor={field.name}>
                Időszak vége
              </label>
              <Calendar
                {...field}
                inputId={field.name}
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
        sortField="date"
        sortOrder={-1}
        stripedRows
        value={workedOnResults}
      >
        <Column field="title" header="Esemény neve" sortable />
        <Column
          align="center"
          body={dateBodyTemplate}
          field="date"
          header="Dátum"
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
