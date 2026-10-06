import { useEffect, useMemo, useState } from 'react';

import { useMutation, useQuery } from '@tanstack/react-query';
import { isAxiosError } from 'axios';
import { Divider } from 'primereact/divider';
import { InputMask } from 'primereact/inputmask';
import { InputText } from 'primereact/inputtext';
import { Message } from 'primereact/message';
import { SplitButton } from 'primereact/splitbutton';
import { ToggleButton } from 'primereact/togglebutton';
import { Controller, useForm } from 'react-hook-form';
import type { SubmitHandler } from 'react-hook-form';
import {
  type LoaderFunctionArgs,
  useLoaderData,
  useNavigate,
  useParams,
  useRevalidator,
} from 'react-router';

import { UserNestedList, VideoAdminRetrieve } from 'api/models';
import {
  requestVideoUpdateMutation,
  requestVideoCreateMutation,
} from 'api/mutations';
import { requestVideoRetrieveQuery } from 'api/queries';
import { queryKeys } from 'api/queryKeys';
import AutoCompleteStaff from 'components/AutoCompleteStaff/AutoCompleteStaff';
import FormField from 'components/FormField/FormField';
import LastUpdatedAt from 'components/LastUpdatedAt/LastUpdatedAt';
import { showErrorToast } from 'helpers/showErrorToast';
import { useToast } from 'providers/ToastProvider';
import { queryClient } from 'router';

export interface IVideoCreator {
  additional_data: {
    archiving: {
      hq_archive: boolean;
    };
    coding: {
      website: boolean;
    };
    editing_done: boolean;
    length?: string;
    publishing: {
      website: string;
    };
  };
  editor: UserNestedList | null;
  title: string;
}

export async function loader({ params }: LoaderFunctionArgs) {
  if (params.requestId && params.videoId) {
    return queryClient.query({
      ...requestVideoRetrieveQuery(params.requestId, params.videoId),
      staleTime: 'static',
    });
  }
  return null;
}

const VideoCreatorEditorPage = () => {
  const defaultValues = useMemo(() => {
    return {
      additional_data: {
        archiving: {
          hq_archive: false,
        },
        coding: {
          website: false,
        },
        editing_done: false,
        length: undefined,
        publishing: {
          website: '',
        },
      },
      editor: null,
      id: 0,
      title: '',
    };
  }, []);

  const { control, handleSubmit, reset, setError } = useForm<IVideoCreator>({
    defaultValues,
    mode: 'onChange',
  });
  const { requestId, videoId } = useParams();
  const { showToast } = useToast();
  const { isPending, mutateAsync } = useMutation(
    requestId && videoId
      ? requestVideoUpdateMutation(Number(requestId), Number(videoId))
      : requestVideoCreateMutation(Number(requestId)),
  );
  const query = useQuery({
    ...requestVideoRetrieveQuery(Number(requestId), Number(videoId)),
    enabled: !!requestId && !!videoId,
    refetchInterval: 1000 * 30,
  });
  const {
    data: queryData,
    dataUpdatedAt,
    error,
  } = requestId && videoId
    ? query
    : { data: undefined, dataUpdatedAt: new Date(), error: null };

  const [isDataChanged, setIsDataChanged] = useState<boolean>(false);

  const loaderData = useLoaderData() as VideoAdminRetrieve;
  const navigate = useNavigate();
  const revalidator = useRevalidator();

  const saveButtonItems = [
    {
      command: () => {
        reset();
      },
      icon: 'pi pi-refresh',
      label: 'Visszaállítás',
    },
  ];

  useEffect(() => {
    if (loaderData) {
      setIsDataChanged(false);
      reset({
        ...defaultValues,
        ...loaderData,
        additional_data: {
          ...loaderData.additional_data,
          length: loaderData.additional_data.length
            ? new Date(1000 * loaderData.additional_data.length)
                .toISOString()
                .substring(11, 19)
            : undefined,
        },
      });
    }
  }, [defaultValues, loaderData, reset]);

  useEffect(() => {
    if (requestId && videoId && loaderData !== queryData) {
      setIsDataChanged(true);
    }
  }, [loaderData, queryData, requestId, videoId]);

  const onReload = () => {
    void revalidator.revalidate();
  };

  const onSubmit: SubmitHandler<IVideoCreator> = async (data) => {
    const prevAdditionalData = videoId ? loaderData.additional_data : {};

    let length = null;
    if (data.additional_data.length) {
      const [hours, minutes, seconds] = data.additional_data.length.split(':');
      length = Number(hours) * 60 * 60 + Number(minutes) * 60 + Number(seconds);
    }

    await mutateAsync({
      ...data,
      additional_data: {
        ...prevAdditionalData,
        ...data.additional_data,
        length: length,
      },
      editor: data.editor?.id || null,
    })
      .then(async (response) => {
        showToast({
          detail: `Videó ${requestId ? 'módosítva' : 'létrehozva'}`,
          life: 3000,
          severity: 'success',
          summary: 'Siker',
        });

        if (videoId) {
          await queryClient.invalidateQueries({
            queryKey: queryKeys.video(requestId, videoId),
          });
        } else {
          await queryClient.invalidateQueries({
            queryKey: queryKeys.requestVideos(requestId),
          });
        }

        void navigate(`/requests/${requestId}/videos/${response.data.id}`);
      })
      .catch(async (error) => {
        if (isAxiosError(error)) {
          if (error.response?.status === 404) {
            await queryClient.invalidateQueries({
              queryKey: queryKeys.requestVideos(requestId),
            });
          } else if (error.response?.status === 400) {
            for (const [key, value] of Object.entries(error.response.data)) {
              // @ts-expect-error: Correct types will be sent in the API error response
              setError(key, { message: value, type: 'backend' });
            }
            return;
          }
        }
        showErrorToast(error);
      });
  };

  useEffect(() => {
    if (!error) return;
    if (isAxiosError(error)) {
      void navigate('/error', {
        state: {
          statusCode: error.response?.status,
          statusText: error.response?.statusText,
        },
      });
    } else {
      showErrorToast(error);
    }
  }, [error, navigate]);

  return (
    <div className="p-3 sm:p-5 surface-ground">
      <div className="font-medium mb-3 text-900 text-xl">Videó létrehozása</div>
      <form className="border-round p-3 p-fluid shadow-2 sm:p-4 surface-card">
        <div className="formgrid grid p-fluid">
          {isDataChanged && (
            <Message
              className="mb-4 w-full"
              severity="warn"
              text={
                <>
                  Változás történt az adatokban.{' '}
                  <a
                    className="cursor-pointer hover:dashed underline"
                    onClick={onReload}
                  >
                    Újratöltés
                  </a>
                </>
              }
            />
          )}
          <FormField
            className="col-12 mb-0"
            control={control}
            disabled={isPending}
            label="Videó címe"
            name="title"
            rules={{
              maxLength: 200,
              required: true,
              validate: (value) => {
                return !!value.trim();
              },
            }}
          >
            <InputText
              autoFocus
              placeholder="Ahogy a weboldalra felkerül"
              type="text"
            />
          </FormField>
          <Divider align="center" type="dashed">
            <b>Opcionális mezők</b>
          </Divider>
          <FormField
            className="col-12 mb-4 md:col-6"
            control={control}
            disabled={isPending}
            label="Vágó"
            name="editor"
          >
            <AutoCompleteStaff />
          </FormField>
          <FormField
            className="col-12 mb-4 md:col-6"
            control={control}
            disabled={isPending}
            icon="pi-clock"
            label="Videó hossza"
            name="additional_data.length"
          >
            <InputMask mask="99:99:99" placeholder="hh:mm:ss" type="text" />
          </FormField>
          <FormField
            className="col-12 mb-0"
            control={control}
            disabled={isPending}
            icon="pi-globe"
            label="Videó elérési útja"
            name="additional_data.publishing.website"
          >
            <InputText
              placeholder="A videó linkje (honlap, YouTube, Google Drive, stb.)"
              type="text"
            />
          </FormField>
          <Divider />
          <Controller
            control={control}
            disabled={isPending}
            name="additional_data.editing_done"
            render={({ field }) => (
              <div className="col-12 mb-3 md:col-4 md:mb-0">
                <ToggleButton
                  {...field}
                  checked={field.value || false}
                  id={field.name}
                  offIcon="bi bi-scissors"
                  offLabel="Vágandó"
                  onChange={field.onChange}
                  onIcon="bi bi-scissors"
                  onLabel="Megvágva"
                  pt={{
                    root: {
                      className: 'w-full',
                    },
                  }}
                  value={undefined}
                />
              </div>
            )}
          />
          <Controller
            control={control}
            disabled={isPending}
            name="additional_data.coding.website"
            render={({ field }) => (
              <div className="col-12 mb-3 md:col-4 md:mb-0">
                <ToggleButton
                  {...field}
                  checked={field.value || false}
                  id={field.name}
                  offIcon="bi bi-file-earmark-play"
                  offLabel="Kódolásra vár"
                  onChange={field.onChange}
                  onIcon="bi bi-file-earmark-play"
                  onLabel="Kikódolva"
                  pt={{
                    root: {
                      className: 'w-full',
                    },
                  }}
                  value={undefined}
                />
              </div>
            )}
          />
          <Controller
            control={control}
            disabled={isPending}
            name="additional_data.archiving.hq_archive"
            render={({ field }) => (
              <div className="col-12 md:col-4">
                <ToggleButton
                  {...field}
                  checked={field.value || false}
                  id={field.name}
                  offIcon="bi bi-archive"
                  offLabel="Archiválandó"
                  onChange={field.onChange}
                  onIcon="bi bi-archive"
                  onLabel="Archiválva"
                  pt={{
                    root: {
                      className: 'w-full',
                    },
                  }}
                  value={undefined}
                />
              </div>
            )}
          />
          <Divider />
          <SplitButton
            className="w-auto"
            icon="pi pi-save"
            label="Mentés"
            loading={isPending}
            model={saveButtonItems}
            onClick={handleSubmit(onSubmit)}
          />
        </div>
      </form>
      <LastUpdatedAt lastUpdatedAt={new Date(dataUpdatedAt)} />
    </div>
  );
};

export { VideoCreatorEditorPage as Component };
