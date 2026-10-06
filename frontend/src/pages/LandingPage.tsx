import { lazy, Suspense, useState } from 'react';

import { useQuery } from '@tanstack/react-query';
import { Column } from 'primereact/column';
import { ConfirmDialog } from 'primereact/confirmdialog';
import { DataTable } from 'primereact/datatable';
import { Divider } from 'primereact/divider';
import { Skeleton } from 'primereact/skeleton';
import { href } from 'react-router';

import { adminApi } from 'api/http';
import { RequestAdminList } from 'api/models/request-admin-list';
import { VideoAdminSearch } from 'api/models/video-admin-search';
import { todosListQuery } from 'api/queries';
import LinkButton from 'components/LinkButton/LinkButton';
import Statistics, {
  StatisticsFieldProps,
} from 'components/Statistics/Statistics';
import { VideoStatusTag } from 'components/StatusTag/StatusTag';
import Todos from 'components/Todos/Todos';
import User from 'components/User/User';
import { dateTimeToLocaleString } from 'helpers/DateToLocaleStringCoverters';
import { getUserId } from 'helpers/LocalStorageHelper';

const AvatarGroupCrew = lazy(() => import('components/Avatar/AvatarGroupCrew'));

const LandingPage = () => {
  const [dates] = useState(() => {
    const now = Date.now();
    return {
      currentDate: new Date(now).toISOString().split('T')[0],
      oneWeekLaterDate: new Date(now + 6048e5).toISOString().split('T')[0],
      twoWeeksLaterDate: new Date(now + 12096e5).toISOString().split('T')[0],
    };
  });

  const { currentDate, oneWeekLaterDate, twoWeeksLaterDate } = dates;

  const { data: notAnsweredData, isLoading: notAnsweredLoading } = useQuery({
    queryFn: async () => {
      const requests = await adminApi.adminRequestsList(
        undefined,
        undefined,
        'start_datetime',
        undefined,
        undefined,
        undefined,
        undefined,
        undefined,
        undefined,
        [1],
      );
      return requests.data.results || [];
    },
    queryKey: ['requests', 'status', '1'],
  });

  const { data: upcomingRecordingData, isLoading: upcomingRecordingLoading } =
    useQuery({
      queryFn: async () => {
        const requests = await adminApi.adminRequestsList(
          undefined,
          undefined,
          'start_datetime',
          undefined,
          undefined,
          undefined,
          undefined,
          currentDate,
          twoWeeksLaterDate,
          [1, 2],
        );
        return requests.data.results || [];
      },
      queryKey: ['requests', `${currentDate}/${twoWeeksLaterDate}`],
    });

  const { data: upcomingDeadlineData, isLoading: upcomingDeadlingLoading } =
    useQuery({
      queryFn: async () => {
        const requests = await adminApi.adminRequestsList(
          undefined,
          oneWeekLaterDate,
          'deadline',
          undefined,
          undefined,
          undefined,
          undefined,
          undefined,
          undefined,
          [3, 4, 5],
        );
        return requests.data.results || [];
      },
      queryKey: ['requests', 'deadline', oneWeekLaterDate],
    });

  const {
    data: requestsWithoutVideosData,
    isLoading: requestsWithoutVideosLoading,
  } = useQuery({
    queryFn: async () => {
      const requests = await adminApi.adminRequestsList(
        undefined,
        undefined,
        'start_datetime',
        undefined,
        undefined,
        undefined,
        undefined,
        undefined,
        undefined,
        [3, 4],
      );
      return (
        requests.data.results?.filter((request) => request.video_count == 0) ||
        []
      );
    },
    queryKey: ['requests', 'videos_count', '0'],
  });

  const { data: notEditedVideosData, isLoading: notEditedVideosLoading } =
    useQuery({
      queryFn: async () => {
        const requests = await adminApi.adminVideosList(
          undefined,
          undefined,
          undefined,
          'request__start_datetime',
          undefined,
          undefined,
          undefined,
          undefined,
          undefined,
          undefined,
          [1, 2],
        );
        return requests.data.results || [];
      },
      queryKey: ['videos', 'status', '1,2'],
    });

  const { data: todos, isLoading: todosLoading } = useQuery(
    todosListQuery([getUserId()], 'created', [1]),
  );

  const statistics: StatisticsFieldProps[] = [
    {
      color: 'blue',
      description: 'válaszra vár',
      icon: 'bi bi-envelope-fill',
      loading: notAnsweredLoading,
      title: 'Felkérés',
      value: notAnsweredData?.length.toString() || '0',
    },
    {
      color: 'cyan',
      description: 'a következő két hétben',
      icon: 'bi bi-camera-reels-fill',
      loading: upcomingRecordingLoading,
      title: 'Forgatás',
      value: upcomingRecordingData?.length.toString() || '0',
    },
    {
      color: 'orange',
      description: 'közeleg vagy lejárt',
      icon: 'bi bi-fire',
      loading: upcomingDeadlingLoading,
      title: 'Határidő',
      value: upcomingDeadlineData?.length.toString() || '0',
    },
    {
      color: 'purple',
      description: 'vágandó',
      icon: 'bi bi-scissors',
      loading: notEditedVideosLoading || requestsWithoutVideosLoading,
      title: 'Videó',
      value:
        !!notEditedVideosData && !!requestsWithoutVideosData
          ? (
              notEditedVideosData.length + requestsWithoutVideosData.length
            ).toString()
          : '0',
    },
  ];

  const crewBodyTemplate = ({ crew }: RequestAdminList) => {
    if (!crew.length) return;
    return (
      <Suspense fallback={<Skeleton />}>
        <AvatarGroupCrew className="justify-content-center" crew={crew} />
      </Suspense>
    );
  };

  const dateBodyTemplate = ({ start_datetime }: RequestAdminList) => {
    return dateTimeToLocaleString(new Date(start_datetime), true);
  };

  const deadlineBodyTemplate = ({ deadline }: RequestAdminList) => {
    return dateTimeToLocaleString(new Date(deadline), true);
  };

  const editorBodyTemplate = ({ editor }: VideoAdminSearch) => {
    if (!editor) return;
    return (
      <User
        className="justify-content-center"
        imageUrl={editor.avatar_url}
        name={editor.full_name}
      />
    );
  };

  const responsibleBodyTemplate = ({ responsible }: RequestAdminList) => {
    if (!responsible) return;
    return (
      <User
        className="justify-content-center"
        imageUrl={responsible.avatar_url}
        name={responsible.full_name}
      />
    );
  };

  const requestActionBodyTemplate = ({ id }: RequestAdminList) => {
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

  const videoActionBodyTemplate = ({ id, request_id }: VideoAdminSearch) => {
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

  const videoStatusBodyTemplate = ({
    status,
    status_by_admin,
  }: VideoAdminSearch) => {
    return <VideoStatusTag modified={status_by_admin} statusNum={status} />;
  };

  return (
    <>
      <ConfirmDialog />
      <Statistics statistics={statistics} />
      <div className="p-3 sm:p-5 surface-ground">
        <div className="border-round p-3 shadow-2 sm:p-4 surface-card">
          <div className="grid">
            <div className="col-12 mb-4 md:col-6">
              <div className="align-items-center flex font-medium mb-3 text-900 text-lg">
                <div>Válaszra váró felkérések</div>
              </div>
              <DataTable
                loading={notAnsweredLoading}
                showGridlines
                stripedRows
                value={notAnsweredData}
              >
                <Column header="Esemény neve" field="title" />
                <Column
                  align="center"
                  body={dateBodyTemplate}
                  field="start_datetime"
                  header="Időpont"
                  style={{ whiteSpace: 'nowrap' }}
                />
                <Column
                  body={requestActionBodyTemplate}
                  bodyStyle={{ overflow: 'visible', textAlign: 'center' }}
                  headerStyle={{ textAlign: 'center', width: '4rem' }}
                />
              </DataTable>
            </div>
            <div className="col-12 mb-4 md:col-6">
              <div className="align-items-center flex font-medium mb-3 text-900 text-lg">
                <div>Forgatások a következő két hétben</div>
              </div>
              <DataTable
                loading={upcomingRecordingLoading}
                showGridlines
                stripedRows
                value={upcomingRecordingData}
              >
                <Column header="Esemény neve" field="title" />
                <Column
                  align="center"
                  body={dateBodyTemplate}
                  field="start_datetime"
                  header="Időpont"
                  style={{ whiteSpace: 'nowrap' }}
                />
                <Column
                  alignHeader="center"
                  body={crewBodyTemplate}
                  field="crew"
                  header="Stáb"
                />
                <Column
                  body={requestActionBodyTemplate}
                  bodyStyle={{ overflow: 'visible', textAlign: 'center' }}
                  headerStyle={{ textAlign: 'center', width: '4rem' }}
                />
              </DataTable>
            </div>
            <div className="col-12 mb-4 md:col-6">
              <div className="align-items-center flex font-medium mb-3 text-900 text-lg">
                <div>Közelgő vagy lejárt határidők</div>
              </div>
              <DataTable
                loading={upcomingDeadlingLoading}
                showGridlines
                stripedRows
                value={upcomingDeadlineData}
              >
                <Column header="Esemény neve" field="title" />
                <Column
                  align="center"
                  body={deadlineBodyTemplate}
                  field="deadline"
                  header="Határidő"
                  style={{ whiteSpace: 'nowrap' }}
                />
                <Column
                  alignHeader="center"
                  body={responsibleBodyTemplate}
                  field="responsible"
                  header="Felelős"
                />
                <Column
                  body={requestActionBodyTemplate}
                  bodyStyle={{ overflow: 'visible', textAlign: 'center' }}
                  headerStyle={{ textAlign: 'center', width: '4rem' }}
                />
              </DataTable>
            </div>
            <div className="col-12 mb-4 md:col-6">
              <div className="align-items-center flex font-medium mb-3 text-900 text-lg">
                <div>Vágandó videók</div>
              </div>
              <DataTable
                loading={notEditedVideosLoading}
                showGridlines
                stripedRows
                value={notEditedVideosData}
              >
                <Column header="Videó címe" field="title" />
                <Column
                  align="center"
                  body={videoStatusBodyTemplate}
                  field="status"
                  header="Státusz"
                />
                <Column
                  alignHeader="center"
                  body={editorBodyTemplate}
                  field="editor"
                  header="Vágó"
                />
                <Column
                  body={videoActionBodyTemplate}
                  bodyStyle={{ overflow: 'visible', textAlign: 'center' }}
                  headerStyle={{ textAlign: 'center', width: '4rem' }}
                />
              </DataTable>
              <Divider type="dashed" />
              <p className="font-bold text-xs">
                Az alábbi eseményeknél még nincs videó
              </p>
              <DataTable
                loading={requestsWithoutVideosLoading}
                showGridlines
                stripedRows
                value={requestsWithoutVideosData}
              >
                <Column header="Esemény neve" field="title" />
                <Column
                  align="center"
                  body={dateBodyTemplate}
                  field="start_datetime"
                  header="Időpont"
                  style={{ whiteSpace: 'nowrap' }}
                />
                <Column
                  body={requestActionBodyTemplate}
                  bodyStyle={{ overflow: 'visible', textAlign: 'center' }}
                  headerStyle={{ textAlign: 'center', width: '4rem' }}
                />
              </DataTable>
            </div>
            <div className="col-12 mb-4">
              <div className="align-items-center flex font-medium mb-3 text-900 text-lg">
                <div>Elvégzendő feladataid</div>
              </div>
              <Todos data={todos} loading={todosLoading} />
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export { LandingPage as Component };
