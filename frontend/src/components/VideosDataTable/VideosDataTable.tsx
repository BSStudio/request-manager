import { forwardRef, lazy, Suspense, useState } from 'react';

import { useQuery } from '@tanstack/react-query';
import { Button } from 'primereact/button';
import { Column } from 'primereact/column';
import { DataTable } from 'primereact/datatable';
import type { DataTableProps, DataTableValueArray } from 'primereact/datatable';
import { Rating } from 'primereact/rating';
import { href } from 'react-router';

import { VideoAdminRetrieve } from 'api/models';
import { requestVideosListQuery } from 'api/queries';
import LinkButton from 'components/LinkButton/LinkButton';
import { VideoStatusTag } from 'components/StatusTag/StatusTag';
import User from 'components/User/User';

const RatingDialog = lazy(() => import('components/RatingDialog/RatingDialog'));

type VideosDataTableProps = DataTableProps<DataTableValueArray> & {
  requestId: number;
};

const VideosDataTable = forwardRef<
  React.Ref<HTMLTableElement>,
  VideosDataTableProps
>(({ requestId, ...props }, ref) => {
  const { data, isLoading } = useQuery(requestVideosListQuery(requestId));

  const [ratingDialogIsRated, setRatingDialogIsRated] =
    useState<boolean>(false);
  const [ratingDialogVideoId, setRatingDialogVideoId] = useState<number>(0);
  const [ratingDialogVideoTitle, setRatingDialogVideoTitle] =
    useState<string>('');
  const [ratingDialogVisible, setRatingDialogVisible] =
    useState<boolean>(false);

  const editorBodyTemplate = ({ editor }: VideoAdminRetrieve) => {
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
  }: VideoAdminRetrieve) => {
    return <VideoStatusTag modified={status_by_admin} statusNum={status} />;
  };

  const ratingBodyTemplate = ({ avg_rating }: VideoAdminRetrieve) => {
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

  const actionBodyTemplate = ({
    id,
    rated,
    status,
    title,
  }: VideoAdminRetrieve) => {
    return (
      <div>
        <Button
          aria-label="Értékelés"
          className="mr-2 p-button-outlined"
          disabled={status < 3}
          icon={rated ? 'pi pi-star-fill' : 'pi pi-star'}
          onClick={() => {
            setRatingDialogIsRated(rated);
            setRatingDialogVideoId(id);
            setRatingDialogVideoTitle(title);
            setRatingDialogVisible(true);
          }}
        />
        <LinkButton
          buttonProps={{
            'aria-label': 'Ugrás a videóhoz',
            className: 'p-button-outlined',
            icon: 'pi pi-sign-in',
          }}
          linkProps={{
            to: href('/requests/:requestId/videos/:videoId', {
              requestId: requestId.toString(),
              videoId: id.toString(),
            }),
          }}
        />
      </div>
    );
  };

  return (
    <>
      <DataTable
        dataKey="id"
        emptyMessage="Nem található videó."
        loading={isLoading}
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
          alignHeader="center"
          body={editorBodyTemplate}
          field="editor"
          header="Vágó"
          sortable
          sortField="editor.full_name"
          style={{ minWidth: '10rem', width: '25%' }}
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
          headerStyle={{ minWidth: '10rem', textAlign: 'center', width: '10%' }}
        />
      </DataTable>
      <Suspense>
        <RatingDialog
          isRated={ratingDialogIsRated}
          onHide={() => {
            setRatingDialogVisible(false);
          }}
          requestId={requestId}
          videoId={ratingDialogVideoId}
          videoTitle={ratingDialogVideoTitle}
          visible={ratingDialogVisible}
        />
      </Suspense>
    </>
  );
});
VideosDataTable.displayName = 'VideosDataTable';

export default VideosDataTable;
