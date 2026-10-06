import { Suspense, lazy, useRef, useState } from 'react';

import { useMutation, useSuspenseQuery } from '@tanstack/react-query';
import { isAxiosError } from 'axios';
import { Button } from 'primereact/button';
import { Chip } from 'primereact/chip';
import { ConfirmDialog, confirmDialog } from 'primereact/confirmdialog';
import { ProgressBar } from 'primereact/progressbar';
import { StyleClass } from 'primereact/styleclass';
import { TabView, TabPanel } from 'primereact/tabview';
import { Tag } from 'primereact/tag';
import { classNames } from 'primereact/utils';
import { href, useNavigate, useParams } from 'react-router';

import {
  requestVideoDeleteMutation,
  requestVideoUpdateMutation,
} from 'api/mutations';
import { requestVideoRetrieveQuery } from 'api/queries';
import { queryKeys } from 'api/queryKeys';
import DetailsRow from 'components/Details/DetailsRow';
import LastUpdatedAt from 'components/LastUpdatedAt/LastUpdatedAt';
import LinkButton from 'components/LinkButton/LinkButton';
import { VideoStatusTag } from 'components/StatusTag/StatusTag';
import User from 'components/User/User';
import { showErrorToast } from 'helpers/showErrorToast';
import useMobile from 'hooks/useMobile';
import { queryClient } from 'router';

const AdditionalDataDialog = lazy(
  () => import('components/AdditionalDataDialog/AdditionalDataDialog'),
);
const AiredAddDialog = lazy(
  () => import('components/Details/Video/AiredAddDialog'),
);
const Ratings = lazy(() => import('components/Details/Video/Ratings'));
const Todos = lazy(() => import('components/Todos/Todos'));
const VideoHistory = lazy(() => import('components/History/VideoHistory'));
const VideoStatusHelperSlideover = lazy(
  () => import('components/StatusHelperSlideover/VideoStatusHelperSlideover'),
);

const VideoDetailsPage = () => {
  const { requestId, videoId } = useParams();
  const { mutateAsync } = useMutation(
    requestVideoUpdateMutation(Number(requestId), Number(videoId)),
  );
  const { mutateAsync: deleteVideo } = useMutation(
    requestVideoDeleteMutation(Number(requestId), Number(videoId)),
  );
  const isMobile = useMobile();
  const navigate = useNavigate();

  const {
    data: queryResult,
    dataUpdatedAt,
    refetch,
  } = useSuspenseQuery(
    requestVideoRetrieveQuery(Number(requestId), Number(videoId)),
  );

  const [additionalDataDialogError, setAdditionalDataDialogError] =
    useState('');
  const [additionalDataDialogOpen, setAdditionalDataDialogOpen] =
    useState(false);
  const [airedAddDialogOpen, setAiredAddDialogOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const statusHelperSlideoverOpenBtnRef = useRef(null);

  const handleDelete = async () => {
    setLoading(true);

    await deleteVideo()
      .then(() => {
        void navigate(`/requests/${requestId}/videos`, { replace: true });
        void queryClient.invalidateQueries({
          queryKey: queryKeys.requestVideos(requestId),
        });
        void queryClient.invalidateQueries({
          queryKey: queryKeys.video(requestId, videoId),
        });
      })
      .catch((error) => {
        if (isAxiosError(error) && error.response?.status === 404) {
          void navigate(`/requests/${requestId}/videos`, { replace: true });
          void queryClient.invalidateQueries({
            queryKey: queryKeys.requestVideos(requestId),
          });
          void queryClient.invalidateQueries({
            queryKey: queryKeys.video(requestId, videoId),
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
          queryKey: queryKeys.video(requestId, videoId),
        });
        setAdditionalDataDialogOpen(false);
      })
      .catch(async (error) => {
        if (isAxiosError(error)) {
          if (error.response?.status === 404) {
            await queryClient.invalidateQueries({
              queryKey: queryKeys.video(requestId, videoId),
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

  const onAiredDateRemove = (airedDate: string) => {
    setLoading(true);

    const aired = (queryResult.additional_data.aired || []).filter(
      (element: string) => element !== airedDate,
    );

    mutateAsync({
      additional_data: {
        ...queryResult.additional_data,
        aired: aired,
      },
    })
      .then(async () => {
        await queryClient.invalidateQueries({
          queryKey: queryKeys.video(requestId, videoId),
        });
      })
      .catch(async (error) => {
        if (isAxiosError(error) && error.response?.status === 404) {
          await queryClient.invalidateQueries({
            queryKey: queryKeys.video(requestId, videoId),
          });
        }
        showErrorToast(error);
      })
      .finally(() => {
        setLoading(false);
      });

    return true;
  };

  const onAiredDateSave = async (data: { airedDate: Date }) => {
    setLoading(true);

    const aired = queryResult.additional_data.aired || [];
    const offset = data.airedDate.getTimezoneOffset();
    const newAiredDate = new Date(
      data.airedDate.getTime() - offset * 60 * 1000,
    );
    aired.push(newAiredDate.toISOString().split('T')[0]);

    await mutateAsync({
      additional_data: {
        ...queryResult.additional_data,
        aired: aired,
      },
    })
      .then(async () => {
        await queryClient.invalidateQueries({
          queryKey: queryKeys.video(requestId, videoId),
        });
        setAiredAddDialogOpen(false);
      })
      .catch(async (error) => {
        if (isAxiosError(error) && error.response?.status === 404) {
          await queryClient.invalidateQueries({
            queryKey: queryKeys.video(requestId, videoId),
          });
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
      header: 'Biztosan törölni akarod a videót?',
      icon: 'pi pi-exclamation-triangle',
      message:
        'A videó törlésével az összes értékelés is törlésre kerül. A művelet visszavonhatatlan!',
      style: { width: '50vw' },
    });
  };

  return (
    <>
      <Suspense>
        <AdditionalDataDialog
          data={queryResult.additional_data}
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
        <AiredAddDialog
          loading={loading}
          onHide={() => {
            setAiredAddDialogOpen(false);
          }}
          onSave={onAiredDateSave}
          visible={airedAddDialogOpen}
        />
      </Suspense>
      <Suspense>
        <VideoStatusHelperSlideover
          adminStatusOverride={
            !!queryResult.additional_data.status_by_admin?.status
          }
          editor={!!queryResult.editor}
          id="videoStatusHelper"
          status={queryResult.status}
        />
      </Suspense>
      <ConfirmDialog />
      <div className="p-3 sm:p-5 surface-ground">
        <div className="flex flex-column mb-3 sm:align-items-center sm:flex-row sm:justify-content-between">
          <div>
            <div className="font-medium mb-2 text-900 text-xl">
              {queryResult.title}
            </div>
            <div className="font-medium mb-3 sm:mb-0 text-500 text-sm">
              <VideoStatusTag
                modified={!!queryResult.additional_data.status_by_admin?.status}
                statusNum={queryResult.status}
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
              selector="#videoStatusHelper"
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
            <LinkButton
              buttonProps={{
                className: 'mr-2 p-button p-button-rounded',
                icon: 'pi pi-pencil',
              }}
              linkProps={{
                to: href('/requests/:requestId/videos/:videoId/edit', {
                  requestId: requestId?.toString(),
                  videoId: videoId?.toString(),
                }),
              }}
            />
            <Button
              className="p-button-danger p-button-rounded"
              icon="pi pi-trash"
              onClick={onDelete}
            />
          </div>
        </div>
        <div className="border-round p-2 shadow-2 sm:p-3 surface-card">
          <ul className="list-none p-0 m-0">
            <DetailsRow
              content={queryResult.title}
              firstElement
              label="Videó címe"
            />
            <DetailsRow
              content={
                <VideoStatusTag
                  modified={
                    !!queryResult.additional_data.status_by_admin?.status
                  }
                  statusNum={queryResult.status}
                />
              }
              label="Státusz"
            />
            <DetailsRow
              button={
                queryResult.editor && (
                  <LinkButton
                    buttonProps={{
                      className: 'p-button-sm p-button-text px-1 py-0',
                      icon: 'pi pi-user',
                      label: 'Profil',
                    }}
                    linkProps={{
                      to: href('/users/:userId', {
                        userId: queryResult.editor.id.toString(),
                      }),
                    }}
                  />
                )
              }
              content={
                queryResult.editor ? (
                  <User
                    name={queryResult.editor.full_name}
                    imageUrl={queryResult.editor.avatar_url}
                  />
                ) : (
                  <Tag
                    className="mr-2"
                    icon="pi pi-exclamation-triangle"
                    severity="warning"
                    value="Nincs vágó"
                  />
                )
              }
              label="Vágó"
            />
            <DetailsRow
              content={
                queryResult.additional_data.length ? (
                  new Date(queryResult.additional_data.length * 1000)
                    .toISOString()
                    .slice(11, 19)
                ) : (
                  <Tag
                    className="mr-2"
                    icon="pi pi-exclamation-triangle"
                    severity="warning"
                    value="Nincs megadva"
                  />
                )
              }
              label="Videó hossza"
            />
            <DetailsRow
              button={
                queryResult.additional_data.publishing?.website ? (
                  <LinkButton
                    buttonProps={{
                      className: 'p-button-sm p-button-text px-1 py-0',
                      icon: 'pi pi-angle-right',
                      label: 'Ugrás',
                    }}
                    linkProps={{
                      rel: 'noopener noreferrer',
                      target: '_blank',
                      to: queryResult.additional_data.publishing.website,
                    }}
                  />
                ) : (
                  <></>
                )
              }
              content={
                queryResult.additional_data.publishing?.website || (
                  <Tag
                    className="mr-2"
                    icon="pi pi-exclamation-triangle"
                    severity="warning"
                    value="Nincs publikálva"
                  />
                )
              }
              label="Elérési út"
            />
            <DetailsRow
              button={
                <Button
                  className="p-button-sm p-button-text px-1 py-0"
                  icon="pi pi-plus"
                  label="Hozzáadás"
                  onClick={() => {
                    setAiredAddDialogOpen(true);
                  }}
                />
              }
              content={
                <div className="flex flex-wrap gap-2">
                  {queryResult.additional_data.aired ? (
                    queryResult.additional_data.aired.map((value: string) => (
                      <Chip
                        key={value}
                        label={value}
                        icon={classNames({ 'pi pi-calendar': !isMobile })}
                        onRemove={() => onAiredDateRemove(value)}
                        removable
                      />
                    ))
                  ) : (
                    <Tag
                      className="mr-2"
                      icon="pi pi-play"
                      severity="info"
                      value="Nem került még adásba"
                    />
                  )}
                </div>
              }
              label="Adásba került"
            />
            <DetailsRow
              content={
                <div className="flex flex-wrap gap-2">
                  <Tag
                    className="mr-2"
                    icon="bi bi-scissors"
                    severity={
                      queryResult.additional_data.editing_done
                        ? 'success'
                        : 'warning'
                    }
                    value={
                      queryResult.additional_data.editing_done
                        ? 'Megvágva'
                        : 'Vágásra vár'
                    }
                  />
                  <Tag
                    className="mr-2"
                    icon="bi bi-file-earmark-play"
                    severity={
                      queryResult.additional_data.coding?.website
                        ? 'success'
                        : 'warning'
                    }
                    value={
                      queryResult.additional_data.coding?.website
                        ? 'Kikódolva'
                        : 'Nincs kikódolva'
                    }
                  />
                  <Tag
                    className="mr-2"
                    icon="bi bi-archive"
                    severity={
                      queryResult.additional_data.archiving?.hq_archive
                        ? 'success'
                        : 'warning'
                    }
                    value={
                      queryResult.additional_data.archiving?.hq_archive
                        ? 'Archiválva'
                        : 'Nincs archiválva'
                    }
                  />
                </div>
              }
              label="Teendők"
            />
          </ul>
          <TabView
            className="pt-3"
            id="ratings-todos-history-tabs"
            panelContainerClassName={classNames(
              'border-bottom-1 surface-border',
              { 'px-0 py-2': isMobile },
            )}
          >
            <TabPanel header="Értékelések" leftIcon="pi pi-star-fill mr-2">
              <Suspense fallback={<ProgressBar mode="indeterminate" />}>
                <div className="md:px-0 pt-3 px-2">
                  <Ratings
                    avgRating={queryResult.avg_rating}
                    isRated={queryResult.rated}
                    requestId={Number(requestId)}
                    videoId={Number(videoId)}
                    videoStatus={queryResult.status}
                    videoTitle={queryResult.title}
                  />
                </div>
              </Suspense>
            </TabPanel>
            <TabPanel header="Feladatok" leftIcon="pi pi-list-check mr-2">
              <Suspense fallback={<ProgressBar mode="indeterminate" />}>
                <Todos
                  requestId={Number(requestId)}
                  showAddButton
                  videoId={Number(videoId)}
                />
              </Suspense>
            </TabPanel>
            <TabPanel header="Előzmények" leftIcon="pi pi-history mr-2">
              <Suspense fallback={<ProgressBar mode="indeterminate" />}>
                <VideoHistory
                  requestId={Number(requestId)}
                  videoId={Number(videoId)}
                />
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

export { VideoDetailsPage as Component };
