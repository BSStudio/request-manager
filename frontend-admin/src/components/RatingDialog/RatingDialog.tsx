import { forwardRef, useEffect, useState } from 'react';

import { useMutation, useQueryClient } from '@tanstack/react-query';
import type { QueryExecuteOptions } from '@tanstack/react-query';
import { isAxiosError } from 'axios';
import { Button } from 'primereact/button';
import { ConfirmPopup, confirmPopup } from 'primereact/confirmpopup';
import { Dialog } from 'primereact/dialog';
import type { DialogProps } from 'primereact/dialog';
import { InputTextarea } from 'primereact/inputtextarea';
import { Message } from 'primereact/message';
import { ProgressSpinner } from 'primereact/progressspinner';
import { Rating } from 'primereact/rating';
import { Tag } from 'primereact/tag';
import { Controller, useForm } from 'react-hook-form';

import { RatingAdminListRetrieve } from 'api/models';
import {
  requestVideoRatingCreateMutation,
  requestVideoRatingDeleteMutation,
  requestVideoRatingUpdateMutation,
} from 'api/mutations';
import {
  requestVideoRatingRetrieveOwnQuery,
  requestVideoRatingRetrieveQuery,
} from 'api/queries';
import { queryKeys } from 'api/queryKeys';
import { getErrorMessage } from 'helpers/ErrorMessageProvider';

interface RatingDialogProps extends DialogProps {
  isRated?: boolean;
  ratingAuthorName?: string;
  ratingId?: number;
  requestId: number;
  videoId: number;
  videoTitle: string;
}

interface IRating {
  rating: number;
  review?: string;
}

const RatingDialog = forwardRef<React.Ref<HTMLDivElement>, RatingDialogProps>(
  (
    {
      isRated,
      onHide,
      ratingAuthorName,
      ratingId: ratingIdParam,
      requestId,
      videoId,
      videoTitle,
      visible,
      ...props
    },
    ref,
  ) => {
    const queryClient = useQueryClient();

    const [loading, setLoading] = useState<boolean>(false);
    const [ratingId, setRatingId] = useState<number>(0);

    const {
      control,
      formState: { isDirty },
      handleSubmit,
      reset,
      setError,
    } = useForm<IRating>({
      shouldFocusError: false,
    });
    const { mutateAsync } = useMutation(
      ratingId
        ? requestVideoRatingUpdateMutation(requestId, videoId, ratingId)
        : requestVideoRatingCreateMutation(requestId, videoId),
    );
    const { mutateAsync: deleteRating } = useMutation(
      requestVideoRatingDeleteMutation(requestId, videoId, ratingId),
    );

    useEffect(() => {
      const fetchData = async (
        query: QueryExecuteOptions<RatingAdminListRetrieve>,
      ) => {
        await queryClient.query(query).then((data) => {
          setRatingId(data.id);
          setLoading(false);
          reset({ ...data });
        });
      };

      let query: QueryExecuteOptions<RatingAdminListRetrieve> | undefined =
        undefined;

      if (visible) {
        const defaultValues: IRating = {
          rating: 0,
          review: '',
        };
        reset({ ...defaultValues });

        if (!ratingIdParam && !isRated) return;

        setLoading(true);
        if (ratingIdParam) {
          query = requestVideoRatingRetrieveQuery(
            requestId,
            videoId,
            ratingIdParam,
          );
        } else if (isRated) {
          query = requestVideoRatingRetrieveOwnQuery(requestId, videoId);
        }

        if (query) {
          fetchData(query).catch(console.error);
        }

        setLoading(false);

        return () => {
          if (query) {
            queryClient
              .cancelQueries({ queryKey: query.queryKey })
              .catch(console.error);
          }
          setTimeout(() => {
            setRatingId(0);
          }, 500);
        };
      }
    }, [
      isRated,
      queryClient,
      ratingIdParam,
      requestId,
      reset,
      videoId,
      visible,
    ]);

    const onSubmit = async (data: IRating) => {
      setLoading(true);

      await mutateAsync({ ...data })
        .then(async (response) => {
          await queryClient.invalidateQueries({
            queryKey: queryKeys.video(requestId, videoId),
          });
          if (!ratingId) {
            setRatingId(response.data.id);
          }
          reset({ ...data });
        })
        .catch(async (error) => {
          // This should mean that the video no longer exists
          if (isAxiosError(error) && error.response?.status === 404) {
            await queryClient.invalidateQueries({
              queryKey: queryKeys.video(requestId, videoId),
            });
          }
          setError('review', {
            message: getErrorMessage(error),
            type: 'backend',
          });
        })
        .finally(() => {
          setLoading(false);
        });
    };

    const handleDelete = async () => {
      setLoading(true);

      await deleteRating()
        .then(async () => {
          await queryClient.invalidateQueries({
            queryKey: queryKeys.video(requestId, videoId),
          });
          onHide();
        })
        .catch(async (error) => {
          if (isAxiosError(error) && error.response?.status === 404) {
            await queryClient.invalidateQueries({
              queryKey: queryKeys.video(requestId, videoId),
            });
          }
          setError('review', {
            message: getErrorMessage(error),
            type: 'backend',
          });
        })
        .finally(() => {
          setLoading(false);
        });
    };

    const onDelete = (event: React.MouseEvent<HTMLButtonElement>) => {
      confirmPopup({
        accept: handleDelete,
        acceptClassName: 'p-button-danger',
        defaultFocus: 'reject',
        icon: 'pi pi-exclamation-triangle',
        message: 'Biztosan törölni akarod az értékelést?',
        target: event.currentTarget,
      });
    };

    const renderFooter = () => {
      return (
        <div>
          <ConfirmPopup />
          {ratingId > 0 && (
            <Button
              className="p-button-text p-button-danger"
              disabled={loading}
              icon="pi pi-trash"
              label="Törlés"
              onClick={onDelete}
            />
          )}
          <Button
            className="p-button-text"
            disabled={loading}
            icon="pi pi-times"
            label="Mégsem"
            onClick={onHide}
          />
          <Button
            autoFocus
            icon="pi pi-check"
            label="Mentés"
            loading={loading}
            onClick={handleSubmit(onSubmit)}
          />
        </div>
      );
    };

    const renderHeader = () => {
      return (
        <div className="align-items-center flex justify-content-start">
          <span style={{ whiteSpace: ratingAuthorName ? 'pre' : 'normal' }}>
            Értékelés{' '}
          </span>
          {ratingAuthorName && (
            <span style={{ color: 'var(--primary-color)' }}>
              - {ratingAuthorName}
            </span>
          )}
          {loading && (
            <ProgressSpinner
              style={{
                height: '1.25rem',
                marginLeft: '1rem',
                width: '1.25rem',
              }}
            />
          )}
        </div>
      );
    };

    return (
      <Dialog
        closeOnEscape={!isDirty}
        breakpoints={{ '768px': '95vw' }}
        footer={renderFooter}
        header={renderHeader}
        onHide={onHide}
        style={{ width: '50vw' }}
        visible={visible}
        {...props}
        {...ref}
      >
        <form className="formgrid grid p-fluid">
          <div className="field col-12">
            <label
              className="align-items-center flex font-medium text-900 text-sm"
              htmlFor="rating"
            >
              Hogy tetszett a(z) <Tag className="mx-1">{videoTitle}</Tag> videó?
            </label>
            <Controller
              control={control}
              disabled={loading}
              name="rating"
              render={({ field, fieldState }) => (
                <div className="align-items-center flex justify-content-start">
                  <Rating {...field} cancel={false} id={field.name} />
                  {fieldState.error && (
                    <small
                      className="block p-error pl-2"
                      id={field.name + '-help'}
                    >
                      0 csillagos értékelés nem adható!
                    </small>
                  )}
                </div>
              )}
              rules={{ max: 5, min: 1, required: true }}
            />
          </div>
          <div className="field col-12">
            <label className="font-medium text-900 text-sm" htmlFor="rating">
              Szöveges értékelés
            </label>
            <Controller
              control={control}
              disabled={loading}
              name="review"
              render={({ field, fieldState }) => (
                <>
                  <InputTextarea
                    {...field}
                    autoResize
                    id={field.name}
                    rows={5}
                  />
                  {fieldState.error && (
                    <small className="block p-error" id={field.name + '-help'}>
                      {fieldState.error.message}
                    </small>
                  )}
                </>
              )}
            />
          </div>
          {isDirty && !!ratingId && (
            <div className="col-12">
              <Message
                className="justify-content-start"
                severity="warn"
                text="A módosításaid még nincsenek elmentve!"
              />
            </div>
          )}
        </form>
      </Dialog>
    );
  },
);
RatingDialog.displayName = 'RatingDialog';

export default RatingDialog;
