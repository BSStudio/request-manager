import { lazy, Suspense, useEffect, useRef, useState } from 'react';

import { useMutation, useSuspenseQuery } from '@tanstack/react-query';
import { isAxiosError } from 'axios';
import { Badge } from 'primereact/badge';
import { Button } from 'primereact/button';
import { ConfirmDialog, confirmDialog } from 'primereact/confirmdialog';
import { ProgressBar } from 'primereact/progressbar';
import { StyleClass } from 'primereact/styleclass';
import { TabView, TabPanel } from 'primereact/tabview';
import { Tag } from 'primereact/tag';
import { classNames } from 'primereact/utils';
import { useForm } from 'react-hook-form';
import type { SubmitHandler } from 'react-hook-form';
import { href, useNavigate, useParams } from 'react-router';

import { RequestAdminRetrieve } from 'api/models';
import { requestDeleteMutation, requestUpdateMutation } from 'api/mutations';
import { requestRetrieveQuery } from 'api/queries';
import { queryKeys } from 'api/queryKeys';
import AvatarGroupCrew from 'components/Avatar/AvatarGroupCrew';
import DetailsRow from 'components/Details/DetailsRow';
import JumpButton from 'components/Details/Request/JumpButton';
import {
  RecordingContent,
  RecordingContentButtons,
} from 'components/Details/Request/RecordingContent';
import {
  RequesterContent,
  RequesterContentButtons,
} from 'components/Details/Request/RequesterContent';
import LastUpdatedAt from 'components/LastUpdatedAt/LastUpdatedAt';
import LinkButton from 'components/LinkButton/LinkButton';
import { RequestStatusTag } from 'components/StatusTag/StatusTag';
import User from 'components/User/User';
import {
  dateTimeToLocaleString,
  dateToLocaleString,
} from 'helpers/DateToLocaleStringCoverters';
import { getUserId, isAdmin } from 'helpers/LocalStorageHelper';
import { showErrorToast } from 'helpers/showErrorToast';
import useMobile from 'hooks/useMobile';
import { useToast } from 'providers/ToastProvider';
import { queryClient } from 'router';
import { RequestAdditionalDataRecordingType } from 'types/additionalDataTypes';

const AcceptRejectDialog = lazy(
  () => import('components/Details/Request/AcceptRejectDialog'),
);
const AdditionalDataDialog = lazy(
  () => import('components/AdditionalDataDialog/AdditionalDataDialog'),
);
const CommentCards = lazy(
  () => import('components/Details/Request/CommentCards'),
);
const CrewDataTable = lazy(
  () => import('components/Details/Request/Crew/CrewDataTable'),
);
const RequestHistory = lazy(() => import('components/History/RequestHistory'));
const RequestStatusHelperSlideover = lazy(
  () => import('components/StatusHelperSlideover/RequestStatusHelperSlideover'),
);
const Todos = lazy(() => import('components/Todos/Todos'));
const VideosDataTable = lazy(
  () => import('components/VideosDataTable/VideosDataTable'),
);

interface RequestAdminRetrieveDates // TODO: Rename?
  extends Omit<
    RequestAdminRetrieve,
    'created' | 'deadline' | 'end_datetime' | 'start_datetime'
  > {
  created: Date;
  deadline: Date;
  end_datetime: Date;
  start_datetime: Date;
}

const RequestDetailsPage = () => {
  const { requestId } = useParams();
  const { showToast } = useToast();
  const { mutateAsync } = useMutation(requestUpdateMutation(Number(requestId)));
  const { mutateAsync: deleteRequest } = useMutation(
    requestDeleteMutation(Number(requestId)),
  );
  const isMobile = useMobile();
  const navigate = useNavigate();

  const getRequest = (
    data: RequestAdminRetrieve,
  ): RequestAdminRetrieveDates => {
    return {
      ...data,
      created: new Date(data.created),
      deadline: new Date(data.deadline),
      end_datetime: new Date(data.end_datetime),
      start_datetime: new Date(data.start_datetime),
    };
  };

  const {
    data: queryResult,
    dataUpdatedAt,
    refetch,
  } = useSuspenseQuery(requestRetrieveQuery(Number(requestId)));
  const data = getRequest(queryResult);

  const [acceptRejectDialogOpen, setAcceptRejectDialogOpen] = useState(false);
  const [additionalDataDialogError, setAdditionalDataDialogError] =
    useState('');
  const [additionalDataDialogOpen, setAdditionalDataDialogOpen] =
    useState(false);
  const [recordingIsEditing, setRecordingIsEditing] = useState(false);
  const [loading, setLoading] = useState(false);
  const [tabViewActiveIndex, setTabViewActiveIndex] = useState(0);
  const statusHelperSlideoverOpenBtnRef = useRef(null);

  const generateRecordingPath = () => {
    return `N://${data.start_datetime
      .toISOString()
      .slice(0, 10)
      .replace(/-/g, '')}_${data.title
      .normalize('NFD')
      .replace(/([\u0300-\u036f]|[^0-9a-zA-Z\s])/g, '')
      .toLowerCase()
      .split(' ')
      .join('_')}`.replace(/_{2,}/, '_');
  };

  const getCalendarUrl = () => {
    const endDate = data.end_datetime
      .toISOString()
      .slice(0, 10)
      .replace(/-/g, '');
    const startDate = data.start_datetime
      .toISOString()
      .slice(0, 10)
      .replace(/-/g, '');
    return `https://calendar.google.com/calendar/embed?src=8kvtmormo2672mftkmmhc8qvk4@group.calendar.google.com&ctz=Europe/Budapest&mode=week&dates=${startDate}/${endDate}`;
  };

  const handleDelete = async () => {
    setLoading(true);
    await deleteRequest()
      .then(() => {
        void navigate('/requests', { replace: true });
        void queryClient.invalidateQueries({ queryKey: queryKeys.requests() });
        void queryClient.invalidateQueries({
          queryKey: queryKeys.request(requestId),
        });
      })
      .catch((error) => {
        if (isAxiosError(error) && error.response?.status === 404) {
          void navigate('/requests', { replace: true });
          void queryClient.invalidateQueries({
            queryKey: queryKeys.requests(),
          });
          void queryClient.invalidateQueries({
            queryKey: queryKeys.request(requestId),
          });
        }
        showErrorToast(error);
      })
      .finally(() => {
        setLoading(false);
      });
  };

  const onAcceptRejectSave = async (data: {
    accepted: boolean | null;
    canceled: boolean | null;
    failed: boolean | null;
  }) => {
    setLoading(true);

    // Do this to consistently remove unused keys
    const _data = {
      ...data,
      canceled: data.canceled || null,
      failed: data.failed || null,
    };

    await mutateAsync({
      additional_data: { ...queryResult.additional_data, ..._data },
    })
      .then(async () => {
        await queryClient.invalidateQueries({
          queryKey: queryKeys.request(requestId),
        });
        setAcceptRejectDialogOpen(false);
        showToast({
          detail:
            'Állapotot változtattál. Ne felejtsd el értesíteni a felkérőt!',
          severity: 'info',
          sticky: true,
          summary: 'Információ',
        });
      })
      .catch(async (error) => {
        if (isAxiosError(error) && error.response?.status === 404) {
          await queryClient.invalidateQueries({
            queryKey: queryKeys.request(requestId),
          });
        }
        showErrorToast(error);
      })
      .finally(() => {
        setLoading(false);
      });
  };

  const onAdditionalDataSave = async (data: { additional_data: string }) => {
    setLoading(true);

    let additional_data: object;

    try {
      additional_data = JSON.parse(data.additional_data);
    } catch (error) {
      if (error instanceof SyntaxError) {
        setAdditionalDataDialogError(error.message);
      }
      setLoading(false);
      return;
    }

    await mutateAsync({ additional_data: additional_data })
      .then(async () => {
        await queryClient.invalidateQueries({
          queryKey: queryKeys.request(requestId),
        });
        setAdditionalDataDialogOpen(false);
      })
      .catch(async (error) => {
        if (isAxiosError(error)) {
          if (error.response?.status === 404) {
            await queryClient.invalidateQueries({
              queryKey: queryKeys.request(requestId),
            });
          } else if (error.response?.status === 400) {
            setAdditionalDataDialogError(error.response.data?.additional_data);
            return;
          }
        }
        showErrorToast(error);
      })
      .finally(() => {
        setLoading(false);
      });
  };

  const onDelete = () => {
    confirmDialog({
      accept: handleDelete,
      acceptClassName: 'p-button-danger',
      breakpoints: { '768px': '95vw' },
      defaultFocus: 'reject',
      header: 'Biztosan törölni akarod a felkérést?',
      icon: 'pi pi-exclamation-triangle',
      message:
        'A felkérés törlésével az összes videó, stábtag, hozzászólás és értékelés is törlésre kerül. A művelet visszavonhatatlan!',
      style: { width: '50vw' },
    });
  };

  const onJumpToTabView = (tabViewIndex: number) => {
    setTabViewActiveIndex(tabViewIndex);
    const tabViewEl = document.getElementById(
      'comments-crew-videos-todos-history-tabs',
    );
    // Workaround for: https://github.com/primefaces/primereact/issues/4034
    setTimeout(() => {
      tabViewEl?.scrollIntoView({ behavior: 'smooth' });
    }, 5);
  };

  const videoDataHeader = (
    <div
      className={classNames(
        'align-items-center flex flex-wrap',
        isMobile ? 'justify-content-start' : ' justify-content-end',
      )}
    >
      <LinkButton
        buttonProps={{
          className: isMobile ? 'w-full' : '',
          icon: 'pi pi-plus',
          label: 'Új videó',
        }}
        linkProps={{
          className: isMobile ? 'w-full' : '',
          to: href('/requests/:requestId/videos/new', {
            requestId: data.id.toString(),
          }),
        }}
      />
    </div>
  );

  const {
    control: recordingContentControl,
    handleSubmit: recordingContentHandleSubmit,
    reset: recordingContentReset,
  } = useForm<RequestAdditionalDataRecordingType>({
    defaultValues: {
      copied_to_gdrive: data.additional_data.recording?.copied_to_gdrive,
      path: data.additional_data.recording?.path,
      removed: data.additional_data.recording?.removed,
    },
  });

  const onSubmitRecordingContent: SubmitHandler<
    RequestAdditionalDataRecordingType
  > = async (data) => {
    setLoading(true);

    await mutateAsync({
      additional_data: {
        ...queryResult.additional_data,
        recording: { ...queryResult.additional_data.recording, ...data },
      },
    })
      .then(async () => {
        await queryClient.invalidateQueries({
          queryKey: queryKeys.request(requestId),
        });
        setRecordingIsEditing(false);
      })
      .catch(async (error) => {
        if (isAxiosError(error) && error.response?.status === 404) {
          await queryClient.invalidateQueries({
            queryKey: queryKeys.request(requestId),
          });
        }
        showErrorToast(error);
      })
      .finally(() => {
        setLoading(false);
      });
  };

  const onRecordingDataCancel = () => {
    setRecordingIsEditing(false);
    recordingContentReset();
  };

  useEffect(() => {
    // Workaround for: https://github.com/primefaces/primereact/issues/4034
    window.scrollTo(0, 0);
  }, []);

  return (
    <>
      <ConfirmDialog />
      <Suspense>
        <AcceptRejectDialog
          accepted={data.additional_data.accepted}
          canceled={data.additional_data.canceled}
          loading={loading}
          failed={data.additional_data.failed}
          onHide={() => {
            setAcceptRejectDialogOpen(false);
          }}
          onSave={onAcceptRejectSave}
          visible={acceptRejectDialogOpen}
        />
      </Suspense>
      <Suspense>
        <AdditionalDataDialog
          data={data.additional_data}
          error={additionalDataDialogError}
          loading={loading}
          onHide={() => {
            setAdditionalDataDialogOpen(false);
          }}
          onSave={onAdditionalDataSave}
          visible={additionalDataDialogOpen}
        />
      </Suspense>
      <Suspense>
        <RequestStatusHelperSlideover
          adminStatusOverride={!!data.additional_data.status_by_admin?.status}
          allVideosDone={data.videos_edited}
          copiedToDrive={!!data.additional_data.recording?.copied_to_gdrive}
          id="requestStatusHelper"
          status={data.status}
        />
      </Suspense>
      <div className="p-3 sm:p-5 surface-ground">
        <div className="flex flex-column mb-3 sm:align-items-center sm:flex-row sm:justify-content-between">
          <div>
            <div className="font-medium mb-2 text-900 text-xl">
              {data.title}
            </div>
            <div className="font-medium mb-3 sm:mb-0 text-500 text-sm">
              <RequestStatusTag
                modified={!!data.additional_data.status_by_admin?.status}
                statusNum={data.status}
              />
            </div>
          </div>
          <div className="flex">
            <StyleClass
              enterActiveClassName="fadeinleft"
              enterFromClassName="hidden"
              hideOnOutsideClick
              leaveActiveClassName="fadeoutleft"
              leaveToClassName="hidden"
              nodeRef={statusHelperSlideoverOpenBtnRef}
              selector="#requestStatusHelper"
            >
              <Button
                className="mr-2 p-button-rounded p-button-help"
                icon="pi pi-question"
                ref={statusHelperSlideoverOpenBtnRef}
              />
            </StyleClass>
            <Button
              className="mr-2 p-button-rounded p-button-secondary"
              icon="pi pi-sliders-h"
              onClick={() => {
                setAdditionalDataDialogOpen(true);
              }}
            />
            <Button
              className="mr-2 p-button-warning p-button-rounded"
              icon="pi pi-external-link"
              onClick={() => {
                setAcceptRejectDialogOpen(true);
              }}
            />
            <LinkButton
              buttonProps={{
                className: 'mr-2 p-button p-button-rounded',
                icon: 'pi pi-pencil',
              }}
              linkProps={{
                to: href('/requests/:requestId/edit', {
                  requestId: requestId,
                }),
              }}
            />
            <Button
              className="p-button-danger p-button-rounded"
              disabled={!isAdmin() && data.requested_by.id !== getUserId()}
              icon="pi pi-trash"
              onClick={onDelete}
            />
          </div>
        </div>
        <div className="border-round p-2 shadow-2 sm:p-3 surface-card">
          <ul className="list-none p-0 m-0">
            <DetailsRow
              content={data.title}
              firstElement
              label="Esemény neve"
            />
            <DetailsRow
              content={
                <RequestStatusTag
                  modified={!!data.additional_data.status_by_admin?.status}
                  statusNum={data.status}
                />
              }
              label="Státusz"
            />
            <DetailsRow
              button={
                <LinkButton
                  buttonProps={{
                    className: 'p-button-sm p-button-text px-1 py-0',
                    icon: 'pi pi-calendar',
                    label: 'Naptár',
                  }}
                  linkProps={{
                    rel: 'noopener noreferrer',
                    target: '_blank',
                    to: getCalendarUrl(),
                  }}
                />
              }
              content={dateTimeToLocaleString(data.start_datetime)}
              label="Kezdés időpontja"
            />
            <DetailsRow
              content={dateTimeToLocaleString(data.end_datetime)}
              label="Várható befejezés"
            />
            <DetailsRow content={data.place} label="Helyszín" />
            <DetailsRow content={data.type} label="Típus" />
            <DetailsRow
              button={
                <RequesterContentButtons
                  requestTitle={data.title}
                  requester={data.requester}
                />
              }
              content={
                <RequesterContent
                  additionalData={data.additional_data}
                  requester={data.requester}
                />
              }
              label="Felkérő"
            />
            <DetailsRow
              content={dateToLocaleString(data.deadline)}
              label="Határidő"
            />
            <DetailsRow
              button={
                data.responsible && (
                  <LinkButton
                    buttonProps={{
                      className: 'p-button-sm p-button-text px-1 py-0',
                      icon: 'pi pi-user',
                      label: 'Profil',
                    }}
                    linkProps={{
                      to: href('/users/:userId', {
                        userId: data.responsible.id.toString(),
                      }),
                    }}
                  />
                )
              }
              content={
                data.responsible ? (
                  <User
                    name={data.responsible.full_name}
                    imageUrl={data.responsible.avatar_url}
                  />
                ) : (
                  <Tag
                    className="mr-2"
                    icon="pi pi-exclamation-triangle"
                    severity="warning"
                    value="Nincs felelős"
                  />
                )
              }
              label="Felelős"
            />
            <DetailsRow
              button={
                <JumpButton
                  onClick={() => {
                    onJumpToTabView(0);
                  }}
                />
              }
              content={
                <Badge
                  severity={data.comment_count > 0 ? 'warning' : 'info'}
                  value={data.comment_count}
                />
              }
              label="Hozzászólások"
            />
            <DetailsRow
              button={
                <JumpButton
                  onClick={() => {
                    onJumpToTabView(1);
                  }}
                />
              }
              content={
                data.crew && data.crew.length > 0 ? (
                  <AvatarGroupCrew crew={data.crew} />
                ) : (
                  <Tag
                    className="mr-2"
                    icon="pi pi-exclamation-triangle"
                    severity="warning"
                    value="Nincs stáb"
                  />
                )
              }
              label="Stáb"
            />
            <DetailsRow
              button={
                <RecordingContentButtons
                  editing={recordingIsEditing}
                  editOnCancel={() => {
                    onRecordingDataCancel();
                  }}
                  editOnClick={() => {
                    setRecordingIsEditing(true);
                  }}
                  editOnSave={recordingContentHandleSubmit(
                    onSubmitRecordingContent,
                  )}
                  loading={loading}
                  recordingPath={data.additional_data.recording?.path}
                />
              }
              content={
                <RecordingContent
                  control={recordingContentControl}
                  copied_to_gdrive={
                    data.additional_data.recording?.copied_to_gdrive
                  }
                  editing={recordingIsEditing}
                  loading={loading}
                  path={data.additional_data.recording?.path}
                  recommendedPath={generateRecordingPath()}
                  removed={data.additional_data.recording?.removed}
                />
              }
              label="Nyersek"
            />
            <DetailsRow
              button={
                <JumpButton
                  onClick={() => {
                    onJumpToTabView(2);
                  }}
                />
              }
              content={
                <Badge
                  value={data.video_count}
                  severity={data.video_count > 0 ? 'success' : 'danger'}
                />
              }
              label="Videók"
            />
            <DetailsRow
              button={
                <LinkButton
                  buttonProps={{
                    className: 'p-button-sm p-button-text px-1 py-0',
                    icon: 'pi pi-user',
                    label: 'Profil',
                  }}
                  linkProps={{
                    to: href('/users/:userId', {
                      userId: data.requested_by.id.toString(),
                    }),
                  }}
                />
              }
              content={
                <User
                  name={data.requested_by.full_name}
                  imageUrl={data.requested_by.avatar_url}
                />
              }
              label="Beküldő"
            />
            <DetailsRow
              content={dateTimeToLocaleString(data.created)}
              label="Beküldve"
            />
          </ul>
          <TabView
            activeIndex={tabViewActiveIndex}
            className="pt-3"
            id="comments-crew-videos-todos-history-tabs"
            onTabChange={(e) => {
              setTabViewActiveIndex(e.index);
            }}
            panelContainerClassName={classNames(
              'border-bottom-1 surface-border',
              { 'px-0 py-2': isMobile },
            )}
          >
            <TabPanel header="Hozzászólások" leftIcon="pi pi-comments mr-2">
              <Suspense fallback={<ProgressBar mode="indeterminate" />}>
                <CommentCards
                  requestId={data.id}
                  requesterId={data.requester.id}
                />
              </Suspense>
            </TabPanel>
            <TabPanel header="Stáb" leftIcon="pi pi-users mr-2">
              <Suspense fallback={<ProgressBar mode="indeterminate" />}>
                <CrewDataTable requestId={data.id} />
              </Suspense>
            </TabPanel>
            <TabPanel header="Videók" leftIcon="pi pi-video mr-2">
              <Suspense fallback={<ProgressBar mode="indeterminate" />}>
                <VideosDataTable header={videoDataHeader} requestId={data.id} />
              </Suspense>
            </TabPanel>
            <TabPanel header="Feladatok" leftIcon="pi pi-list-check mr-2">
              <Suspense fallback={<ProgressBar mode="indeterminate" />}>
                <Todos requestId={data.id} showAddButton />
              </Suspense>
            </TabPanel>
            <TabPanel header="Előzmények" leftIcon="pi pi-history mr-2">
              <Suspense fallback={<ProgressBar mode="indeterminate" />}>
                <RequestHistory requestId={data.id} />
              </Suspense>
            </TabPanel>
          </TabView>
        </div>
        <LastUpdatedAt
          lastUpdatedAt={new Date(dataUpdatedAt)}
          refetch={refetch}
        />
      </div>
    </>
  );
};

export { RequestDetailsPage as Component };
