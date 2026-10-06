import { forwardRef } from 'react';

import { useQuery } from '@tanstack/react-query';
import { FilterMatchMode } from 'primereact/api';
import { Column } from 'primereact/column';
import type { ColumnFilterElementTemplateOptions } from 'primereact/column';
import { DataTable } from 'primereact/datatable';
import type { DataTableProps, DataTableValueArray } from 'primereact/datatable';
import { TriStateCheckbox } from 'primereact/tristatecheckbox';
import { href } from 'react-router';

import { UserAdminList } from 'api/models';
import { usersListQuery } from 'api/queries';
import LinkButton from 'components/LinkButton/LinkButton';
import User from 'components/User/User';

import stylesModule from './UsersDataTable.module.css';

const UsersDataTable = forwardRef<
  React.Ref<HTMLTableElement>,
  DataTableProps<DataTableValueArray>
>((props, ref) => {
  const { data, isLoading } = useQuery(usersListQuery());

  const isStaffBodyTemplate = ({ is_staff }: UserAdminList) => {
    return (
      <i
        className={
          is_staff
            ? 'true-icon pi pi-check-circle text-green-500'
            : 'false-icon pi pi-times-circle text-pink-500'
        }
      ></i>
    );
  };

  const fullNameBodyTemplate = ({ avatar_url, full_name }: UserAdminList) => {
    return <User imageUrl={avatar_url} name={full_name} />;
  };

  const actionBodyTemplate = ({ id }: UserAdminList) => {
    return (
      <LinkButton
        buttonProps={{
          'aria-label': 'Ugrás a profilra',
          className: 'p-button-outlined',
          icon: 'pi pi-id-card',
        }}
        linkProps={{ to: href('/users/:userId', { userId: id.toString() }) }}
      />
    );
  };

  const isStaffFilterTemplate = (
    options: ColumnFilterElementTemplateOptions,
  ) => {
    function getLabel(value: boolean | null | undefined): string {
      if (value !== null) {
        if (value) return 'BSS tag';
        return 'Nem BSS tag';
      }
      return 'Bármelyik';
    }

    return (
      <div className="field-checkbox m-0">
        <TriStateCheckbox
          onChange={(e) => {
            options.filterCallback(e.value);
          }}
          value={options.value}
        />
        <label>{getLabel(options.value)}</label>
      </div>
    );
  };

  return (
    <DataTable
      dataKey="id"
      emptyMessage="Nem található felhasználó."
      loading={isLoading}
      paginator
      rows={25}
      rowsPerPageOptions={[10, 25, 50, 100]}
      showGridlines
      sortField="full_name"
      sortOrder={1}
      stripedRows
      value={data}
      {...props}
      {...ref}
    >
      <Column
        body={fullNameBodyTemplate}
        field="full_name"
        filter
        filterMatchMode={FilterMatchMode.CONTAINS}
        header="Név"
        sortable
      />
      <Column
        field="email"
        filter
        filterMatchMode={FilterMatchMode.CONTAINS}
        header="E-mail"
        sortable
      />
      <Column
        field="phone_number"
        filter
        filterMatchMode={FilterMatchMode.CONTAINS}
        header="Telefonszám"
        sortable
      />
      <Column
        body={isStaffBodyTemplate}
        bodyClassName="text-center"
        dataType="boolean"
        field="is_staff"
        filter
        filterElement={isStaffFilterTemplate}
        filterMatchMode={FilterMatchMode.EQUALS}
        filterMenuClassName={stylesModule.isStaffFilter}
        header="BSS tag"
        showFilterMenuOptions={false}
        showFilterOperator={false}
        sortable
        style={{ minWidth: '8rem' }}
      />
      <Column
        body={actionBodyTemplate}
        bodyStyle={{ overflow: 'visible', textAlign: 'center' }}
        headerStyle={{ textAlign: 'center', width: '4rem' }}
      />
    </DataTable>
  );
});
UsersDataTable.displayName = 'UsersDataTable';

export default UsersDataTable;
