import { forwardRef } from 'react';

import { Column } from 'primereact/column';
import { DataTable } from 'primereact/datatable';
import type { DataTableProps, DataTableValueArray } from 'primereact/datatable';
import { Rating } from 'primereact/rating';
import { href } from 'react-router';

import { VideoAdminSearch } from 'api/models';
import LinkButton from 'components/LinkButton/LinkButton';
import { VideoStatusTag } from 'components/StatusTag/StatusTag';
import User from 'components/User/User';
import { dateToLocaleString } from 'helpers/DateToLocaleStringCoverters';
import useMobile from 'hooks/useMobile';

interface VideoAdminSearchDates // TODO: Rename?
  extends Omit<VideoAdminSearch, 'last_aired' | 'request_start_datetime'> {
  last_aired: Date | null;
  request_start_datetime: Date;
}

type VideoSearchDataTableProps = DataTableProps<DataTableValueArray> & {
  videos: VideoAdminSearch[];
};

const VideoSearchDataTable = forwardRef<
  React.Ref<HTMLTableElement>,
  VideoSearchDataTableProps
>(({ videos, ...props }, ref) => {
  const getVideos = (videos: VideoAdminSearch[]): VideoAdminSearchDates[] => {
    return [...videos].map((video) => {
      return {
        ...video,
        last_aired: video.last_aired ? new Date(video.last_aired) : null,
        request_start_datetime: new Date(video.request_start_datetime),
      };
    });
  };
  const data = getVideos(videos);
  const isMobile = useMobile();

  const dateBodyTemplate = ({
    request_start_datetime,
  }: VideoAdminSearchDates) => {
    return dateToLocaleString(request_start_datetime, isMobile);
  };

  const editorBodyTemplate = ({ editor }: VideoAdminSearchDates) => {
    if (!editor) return;
    return (
      <User
        className="justify-content-center"
        imageUrl={editor.avatar_url}
        name={editor.full_name}
      />
    );
  };

  const statusBodyTemplate = ({
    status,
    status_by_admin,
  }: VideoAdminSearchDates) => {
    return <VideoStatusTag modified={status_by_admin} statusNum={status} />;
  };

  const lastAiredBodyTemplate = ({ last_aired }: VideoAdminSearchDates) => {
    if (!last_aired) return;
    return dateToLocaleString(last_aired, true);
  };

  const lengthBodyTemplate = ({ length }: VideoAdminSearchDates) => {
    if (!length) return;
    return new Date(1000 * length).toISOString().substring(11, 19);
  };

  const ratingBodyTemplate = ({ avg_rating }: VideoAdminSearchDates) => {
    return (
      <Rating
        cancel={false}
        className="justify-content-center"
        tooltip={`${avg_rating || 'Nincs értékelés'}`}
        tooltipOptions={{ className: 'text-xs', position: 'bottom' }}
        readOnly
        value={Math.round(avg_rating)}
      />
    );
  };

  const actionBodyTemplate = ({ id, request_id }: VideoAdminSearchDates) => {
    return (
      <LinkButton
        buttonProps={{
          'aria-label': 'Ugrás a videóhoz',
          className: 'p-button-outlined',
          icon: 'pi pi-sign-in',
        }}
        linkProps={{
          to: href('/requests/:requestId/videos/:videoId', {
            requestId: request_id.toString(),
            videoId: id.toString(),
          }),
        }}
      />
    );
  };

  return (
    <>
      <DataTable
        dataKey="id"
        emptyMessage="Nem található videó."
        showGridlines
        sortField="title"
        sortOrder={1}
        stripedRows
        value={data}
        {...props}
        {...ref}
      >
        <Column
          field="title"
          header="Videó címe"
          sortable
          style={{ minWidth: '10rem', width: '30%' }}
        />
        <Column
          align="center"
          body={statusBodyTemplate}
          field="status"
          header="Státusz"
          sortable
          style={{ minWidth: '5rem', width: '15%' }}
        />
        <Column
          align="center"
          body={dateBodyTemplate}
          dataType="date"
          field="request_start_datetime"
          header="Felkérés kezdése"
          sortable
          style={{ whiteSpace: 'nowrap' }}
        />
        <Column
          alignHeader="center"
          body={editorBodyTemplate}
          field="editor"
          header="Vágó"
          sortable
          sortField="editor.full_name"
          style={{ minWidth: '10rem', width: '25%' }}
        />
        <Column
          align="center"
          body={lastAiredBodyTemplate}
          dataType="date"
          field="last_aired"
          header="Utoljára adásba került"
          sortable
          style={{ whiteSpace: 'nowrap' }}
        />
        <Column
          align="center"
          body={lengthBodyTemplate}
          field="length"
          header="Hossz"
          sortable
          style={{ whiteSpace: 'nowrap' }}
        />
        <Column
          alignHeader="center"
          body={ratingBodyTemplate}
          field="avg_rating"
          header="Értékelések"
          sortable
          style={{ width: '20%' }}
        />
        <Column
          body={actionBodyTemplate}
          bodyStyle={{ overflow: 'visible', textAlign: 'center' }}
          headerStyle={{ textAlign: 'center', width: '4rem' }}
        />
      </DataTable>
    </>
  );
});
VideoSearchDataTable.displayName = 'VideoSearchDataTable';

export default VideoSearchDataTable;
