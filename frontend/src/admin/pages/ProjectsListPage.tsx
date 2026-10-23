import { useState } from 'react';

import { useQuery } from '@tanstack/react-query';
import { Column } from 'primereact/column';
import { DataTable } from 'primereact/datatable';
import type { DataTableExpandedRows } from 'primereact/datatable';
import { IconField } from 'primereact/iconfield';
import { InputIcon } from 'primereact/inputicon';
import { InputText } from 'primereact/inputtext';
import { ProgressBar } from 'primereact/progressbar';
import { href } from 'react-router';

import { projectRequestsListQuery, projectsListQuery } from 'admin/api/queries';
import LastUpdatedAt from 'admin/components/LastUpdatedAt/LastUpdatedAt';
import LinkButton from 'admin/components/LinkButton/LinkButton';
import RequestsDataTable from 'admin/components/RequestsDataTable/RequestsDataTable';
import User from 'admin/components/User/User';
import { dateToLocaleString } from 'admin/helpers/DateToLocaleStringCoverters';
import { ProjectAdminList } from 'api/models';
import { queryClient } from 'api/queryClient';

export async function loader() {
  return queryClient.query({ ...projectsListQuery(), staleTime: 'static' });
}

const ProjectRequests = ({ projectId }: { projectId: number }) => {
  const { data, isLoading } = useQuery(projectRequestsListQuery(projectId));
  if (isLoading) return <ProgressBar mode="indeterminate" />;
  return (
    <RequestsDataTable paginator={false} requests={data ?? []} sortOrder={1} />
  );
};

const ProjectsListPage = () => {
  const [search, setSearch] = useState('');
  const [expandedRows, setExpandedRows] = useState<DataTableExpandedRows>({});
  const { data, dataUpdatedAt, isLoading, refetch } =
    useQuery(projectsListQuery());

  const periodBodyTemplate = ({ first_start, last_end }: ProjectAdminList) => {
    if (!first_start || !last_end) return;
    // The short form, so the range fits on one line.
    return `${dateToLocaleString(new Date(first_start), true)} – ${dateToLocaleString(new Date(last_end), true)}`;
  };

  const responsibleBodyTemplate = ({ responsible }: ProjectAdminList) => {
    if (!responsible) return;
    return (
      <User imageUrl={responsible.avatar_url} name={responsible.full_name} />
    );
  };

  const actionBodyTemplate = ({ id }: ProjectAdminList) => {
    return (
      <LinkButton
        buttonProps={{
          'aria-label': 'Projekt szerkesztése',
          className: 'p-button-outlined',
          icon: 'pi pi-pencil',
        }}
        linkProps={{
          to: href('/projects/:projectId', { projectId: id.toString() }),
        }}
      />
    );
  };

  return (
    <div className="p-3 sm:p-5 surface-ground">
      <div className="align-items-center flex flex-wrap font-medium gap-2 mb-3 text-900 text-xl">
        <div>Projektek</div>
        <IconField className="w-full sm:w-auto" iconPosition="left">
          <InputIcon className="pi pi-search" />
          <InputText
            className="w-full sm:w-20rem"
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Keresés név vagy felelős szerint"
            value={search}
          />
        </IconField>
        <LinkButton
          buttonProps={{ icon: 'pi pi-plus', label: 'Új projekt' }}
          linkProps={{ className: 'ml-auto', to: '/projects/new' }}
        />
      </div>
      <div className="border-round p-3 shadow-2 sm:p-4 surface-card">
        <DataTable
          dataKey="id"
          emptyMessage="Nem található projekt."
          expandedRows={expandedRows}
          globalFilter={search}
          globalFilterFields={['name', 'responsible.full_name']}
          loading={isLoading}
          onRowToggle={(e: { data: DataTableExpandedRows }) => {
            setExpandedRows(e.data);
          }}
          rowExpansionTemplate={({ id }: ProjectAdminList) => (
            <ProjectRequests projectId={id} />
          )}
          showGridlines
          stripedRows
          value={data ?? []}
        >
          <Column
            expander={({ request_count }: ProjectAdminList) =>
              request_count > 0
            }
            style={{ width: '3em' }}
          />
          <Column field="name" header="Projekt neve" />
          <Column
            alignHeader="center"
            body={responsibleBodyTemplate}
            field="responsible"
            header="Felelős"
          />
          <Column align="center" field="request_count" header="Felkérések" />
          <Column
            body={periodBodyTemplate}
            header="Időszak"
            style={{ whiteSpace: 'nowrap' }}
          />
          <Column
            body={actionBodyTemplate}
            bodyStyle={{ overflow: 'visible', textAlign: 'center' }}
            headerStyle={{ textAlign: 'center', width: '4rem' }}
          />
        </DataTable>
      </div>
      {dataUpdatedAt > 0 && (
        <LastUpdatedAt
          lastUpdatedAt={new Date(dataUpdatedAt)}
          refetch={refetch}
        />
      )}
    </div>
  );
};

export { ProjectsListPage as Component };
