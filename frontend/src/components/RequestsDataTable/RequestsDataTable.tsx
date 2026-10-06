import { forwardRef, lazy, Suspense, useState } from 'react';

import { Badge } from 'primereact/badge';
import { Column } from 'primereact/column';
import { DataTable } from 'primereact/datatable';
import type {
  DataTableExpandedRows,
  DataTableProps,
  DataTableValueArray,
} from 'primereact/datatable';
import { ProgressBar } from 'primereact/progressbar';
import { Skeleton } from 'primereact/skeleton';
import { href } from 'react-router';

import { RequestAdminList } from 'api/models';
import LinkButton from 'components/LinkButton/LinkButton';
import { RequestStatusTag } from 'components/StatusTag/StatusTag';
import User from 'components/User/User';
import { dateTimeToLocaleString } from 'helpers/DateToLocaleStringCoverters';
import useMobile from 'hooks/useMobile';

const AvatarGroupCrew = lazy(() => import('components/Avatar/AvatarGroupCrew'));
const VideosDataTable = lazy(
  () => import('components/VideosDataTable/VideosDataTable'),
);

interface RequestAdminListDates // TODO: Rename?
  extends Omit<RequestAdminList, 'created' | 'start_datetime'> {
  created: Date;
  start_datetime: Date;
}

type RequestsDataTableProps = DataTableProps<DataTableValueArray> & {
  requests: RequestAdminList[];
};

const RequestsDataTable = forwardRef<
  React.Ref<HTMLTableElement>,
  RequestsDataTableProps
>(({ requests, ...props }, ref) => {
  const getRequests = (
    requests: RequestAdminList[],
  ): RequestAdminListDates[] => {
    return [...requests].map((request) => {
      return {
        ...request,
        created: new Date(request.created),
        start_datetime: new Date(request.start_datetime),
      };
    });
  };
  const data = getRequests(requests);
  const isMobile = useMobile();

  const [expandedRows, setExpandedRows] = useState<DataTableExpandedRows>({});

  const crewBodyTemplate = ({ crew }: RequestAdminListDates) => {
    if (!crew.length) return;
    return (
      <Suspense fallback={<Skeleton />}>
        <AvatarGroupCrew className="justify-content-center" crew={crew} />
      </Suspense>
    );
  };

  const dateBodyTemplate = ({ start_datetime }: RequestAdminListDates) => {
    return dateTimeToLocaleString(start_datetime, isMobile);
  };

  const responsibleBodyTemplate = ({ responsible }: RequestAdminListDates) => {
    if (!responsible) return;
    return (
      <User
        className="justify-content-center"
        imageUrl={responsible.avatar_url}
        name={responsible.full_name}
      />
    );
  };

  const statusBodyTemplate = ({
    status,
    status_by_admin,
  }: RequestAdminListDates) => {
    return <RequestStatusTag modified={status_by_admin} statusNum={status} />;
  };

  const titleBodyTemplate = ({ created, title }: RequestAdminListDates) => {
    const twoWeeksEarlier = new Date();
    twoWeeksEarlier.setDate(new Date().getDate() - 2 * 7);

    return (
      <div className="align-items-center flex">
        <div className="hyphenate p-overlay-badge">
          {title}
          {created >= twoWeeksEarlier && (
            <Badge className="p-badge-new-request" severity="info"></Badge>
          )}
        </div>
      </div>
    );
  };

  const actionBodyTemplate = ({ id }: RequestAdminListDates) => {
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

  const rowExpansionTemplate = ({ id, video_count }: RequestAdminListDates) => {
    if (!video_count) return;
    return (
      <Suspense fallback={<ProgressBar mode="indeterminate" />}>
        <VideosDataTable requestId={id} />
      </Suspense>
    );
  };

  return (
    <DataTable
      dataKey="id"
      emptyMessage="Nem található felkérés."
      expandedRows={expandedRows}
      onRowToggle={(e: { data: DataTableExpandedRows }) => {
        setExpandedRows(e.data);
      }}
      paginator
      rowExpansionTemplate={rowExpansionTemplate}
      rows={25}
      rowsPerPageOptions={[10, 25, 50, 100]}
      showGridlines
      sortField="start_datetime"
      sortOrder={-1}
      stripedRows
      value={data}
      {...props}
      {...ref}
    >
      <Column
        expander={(rowData: RequestAdminListDates) => rowData.video_count > 0}
        style={{ width: '3em' }}
      />
      <Column
        body={titleBodyTemplate}
        field="title"
        header="Esemény neve"
        sortable
      />
      <Column
        align="center"
        body={statusBodyTemplate}
        field="status"
        header="Státusz"
        sortable
      />
      <Column
        align="center"
        body={dateBodyTemplate}
        dataType="date"
        field="start_datetime"
        header="Kezdés ideje"
        sortable
        style={{ whiteSpace: 'nowrap' }}
      />
      <Column
        alignHeader="center"
        body={responsibleBodyTemplate}
        field="responsible"
        header="Felelős"
        sortable
        sortField="responsible.full_name"
      />
      <Column
        alignHeader="center"
        body={crewBodyTemplate}
        field="crew"
        header="Stáb"
      />
      <Column
        body={actionBodyTemplate}
        bodyStyle={{ overflow: 'visible', textAlign: 'center' }}
        headerStyle={{ textAlign: 'center', width: '4rem' }}
      />
    </DataTable>
  );
});
RequestsDataTable.displayName = 'RequestsDataTable';

export default RequestsDataTable;
