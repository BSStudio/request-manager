import { Suspense, lazy, useEffect, useMemo } from 'react';

import { useMutation, useQuery } from '@tanstack/react-query';
import { isAxiosError } from 'axios';
import { format, parseISO } from 'date-fns';
import { Calendar } from 'primereact/calendar';
import { Checkbox } from 'primereact/checkbox';
import { Divider } from 'primereact/divider';
import { Dropdown } from 'primereact/dropdown';
import { InputText } from 'primereact/inputtext';
import { InputTextarea } from 'primereact/inputtextarea';
import { Message } from 'primereact/message';
import { ProgressBar } from 'primereact/progressbar';
import { SelectButton } from 'primereact/selectbutton';
import { SplitButton } from 'primereact/splitbutton';
import type { IconType } from 'primereact/utils';
import { Controller, useForm, useWatch } from 'react-hook-form';
import type { SubmitHandler } from 'react-hook-form';
import {
  type LoaderFunctionArgs,
  useLoaderData,
  useNavigate,
  useParams,
  useRevalidator,
} from 'react-router';

import {
  requestCreateMutation,
  requestUpdateMutation,
} from 'admin/api/mutations';
import { projectsListQuery, requestRetrieveQuery } from 'admin/api/queries';
import { queryKeys } from 'admin/api/queryKeys';
import AutoCompleteStaff from 'admin/components/AutoCompleteStaff/AutoCompleteStaff';
import FormField from 'admin/components/FormField/FormField';
import LastUpdatedAt from 'admin/components/LastUpdatedAt/LastUpdatedAt';
import NewRequesterForm from 'admin/components/RequestCreator/NewRequesterForm';
import { getErrorMessage } from 'admin/helpers/ErrorMessageProvider';
import { pickDirtyFields } from 'admin/helpers/pickDirtyFields';
import {
  type RequesterValues,
  requesterPayload,
} from 'admin/helpers/requester';
import { requestTypeOptions } from 'admin/helpers/requestTypes';
import { showErrorToast } from 'admin/helpers/showErrorToast';
import useMobile from 'admin/hooks/useMobile';
import type { LoadErrorState } from 'admin/pages/ErrorPage';
import { useToast } from 'admin/providers/ToastProvider';
import { isNotFound, setFieldErrors } from 'api/errors';
import { UserNestedDetail } from 'api/models';
import { queryClient } from 'api/queryClient';
import { getName } from 'helpers/LocalStorageHelper';

const UsersDataTable = lazy(
  () => import('admin/components/UsersDataTable/UsersDataTable'),
);

export interface IRequestCreator extends RequesterValues {
  comment: string;
  createMore: boolean;
  deadline: Date | null;
  end_datetime: Date | null;
  place: string;
  project: number | null;
  responsible: UserNestedDetail | null;
  send_notification: boolean;
  start_datetime: Date | null;
  title: string;
  type: string;
}

export async function loader({ params }: LoaderFunctionArgs) {
  if (params.requestId) {
    return queryClient.query({
      ...requestRetrieveQuery(params.requestId),
      staleTime: 'static',
    });
  }
  return null;
}

const RequestCreatorEditorPage = () => {
  const defaultValues = useMemo((): IRequestCreator => {
    return {
      comment: '',
      createMore: false,
      deadline: null,
      end_datetime: null,
      place: '',
      project: null,
      requester: null,
      requester_email: '',
      requester_first_name: '',
      requester_last_name: '',
      requester_mobile: '',
      requesterType: 'self',
      responsible: null,
      send_notification: false,
      start_datetime: null,
      title: '',
      type: '',
    };
  }, []);

  const {
    control,
    formState: { dirtyFields },
    handleSubmit,
    reset,
    setError,
    setValue,
  } = useForm<IRequestCreator>({
    defaultValues,
    mode: 'onChange',
  });
  const { requestId } = useParams();
  const { showToast } = useToast();
  const { isPending: isCreating, mutateAsync: createRequest } = useMutation(
    requestCreateMutation(),
  );
  const { isPending: isUpdating, mutateAsync: updateRequest } = useMutation(
    requestUpdateMutation(Number(requestId)),
  );
  const isPending = isCreating || isUpdating;
  const { data: projects } = useQuery(projectsListQuery());
  const query = useQuery({
    ...requestRetrieveQuery(Number(requestId)),
    enabled: !!requestId,
    refetchInterval: 1000 * 30,
  });
  const {
    data: queryData,
    dataUpdatedAt,
    error,
  } = requestId
    ? query
    : { data: undefined, dataUpdatedAt: new Date(), error: null };

  const isMobile = useMobile();
  const loaderData = useLoaderData<typeof loader>();
  const isDataChanged = !!requestId && loaderData !== queryData;
  const navigate = useNavigate();
  const revalidator = useRevalidator();

  const watchCreateMore = useWatch({ control, name: 'createMore' });
  const watchRequesterType = useWatch({ control, name: 'requesterType' });

  useEffect(() => {
    if (loaderData) {
      reset({
        ...defaultValues,
        ...loaderData,
        deadline: parseISO(loaderData.deadline),
        end_datetime: new Date(loaderData.end_datetime),
        project: loaderData.project?.id ?? null,
        start_datetime: new Date(loaderData.start_datetime),
      });
    }
  }, [defaultValues, loaderData, reset]);

  const buttonOptions = [
    {
      command: async () => {
        setValue('send_notification', true);
        await handleSubmit(onSubmit)();
      },
      icon: 'pi pi-bell',
      label: 'Mentés értesítéssel',
    },
    {
      command: () => {
        reset();
      },
      icon: 'pi pi-replay',
      label: 'Visszaállítás',
    },
  ];

  const requesterTypeOptions = [
    {
      icon: 'pi pi-user',
      text: loaderData ? loaderData.requester.full_name : getName(),
      value: 'self',
    },
    { icon: 'pi pi-search', text: 'Felhasználó keresése', value: 'search' },
    { icon: 'pi pi-plus', text: 'Új felhasználó hozzáadása', value: 'new' },
  ];

  const requesterTypeOptionTemplate = (option: {
    icon: IconType<IRequestCreator>;
    text: string;
  }) => {
    return (
      <>
        <i className={`${option.icon} pr-2 `}></i>
        <span className="p-button-label p-c">{option.text}</span>
      </>
    );
  };

  const onReload = () => {
    void revalidator.revalidate();
  };

  const onSubmit: SubmitHandler<IRequestCreator> = async (data) => {
    if (!data.start_datetime || !data.end_datetime) return;

    const requester = requesterPayload(data);
    if (!requester) {
      showToast({
        detail: 'Nincs kijelölve felkérő',
        life: 3000,
        severity: 'error',
        summary: 'Hiba',
      });
      return;
    }

    const deadline = data.deadline
      ? format(data.deadline, 'yyyy-MM-dd')
      : undefined;

    const fields = {
      comment: data.comment || undefined,
      deadline: deadline,
      end_datetime: data.end_datetime.toISOString(),
      place: data.place,
      project: data.project ?? null,
      responsible: data.responsible?.id || null,
      start_datetime: data.start_datetime.toISOString(),
      title: data.title,
      type: data.type,
    };

    await (
      requestId
        ? updateRequest({
            ...pickDirtyFields(requester, dirtyFields),
            ...pickDirtyFields(fields, dirtyFields),
            send_notification: data.send_notification,
          })
        : createRequest({
            ...requester,
            ...fields,
            send_notification: data.send_notification,
          })
    )
      .then(async (response) => {
        showToast({
          detail: `Felkérés ${requestId ? 'módosítva' : 'létrehozva'}`,
          life: 3000,
          severity: 'success',
          summary: 'Siker',
        });

        await queryClient.invalidateQueries({
          queryKey: queryKeys.projects(),
        });
        if (requestId) {
          await queryClient.invalidateQueries({
            queryKey: queryKeys.request(requestId),
          });
          await revalidator.revalidate();
        } else {
          await queryClient.invalidateQueries({
            queryKey: queryKeys.requests(),
          });
        }

        if (watchCreateMore) {
          reset();
        } else {
          void navigate('/requests/' + response.data.id);
        }
      })
      .catch(async (error) => {
        if (setFieldErrors(error, setError)) return;
        if (isNotFound(error)) {
          await queryClient.invalidateQueries({
            queryKey: queryKeys.request(requestId),
          });
        }
        showErrorToast(error);
      })
      .finally(() => {
        setValue('send_notification', false);
      });
  };

  useEffect(() => {
    if (!error) return;
    if (isAxiosError(error)) {
      void navigate('/error', {
        state: {
          message: getErrorMessage(error),
          status: error.response?.status,
        } satisfies LoadErrorState,
      });
    } else {
      showErrorToast(error);
    }
  }, [error, navigate]);

  return (
    <div className="p-3 sm:p-5 surface-ground">
      <div className="font-medium mb-3 text-900 text-xl">
        {requestId ? 'Felkérés szerkesztése' : 'Felkérés létrehozása'}
      </div>
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
            className="col-12 mb-4"
            control={control}
            disabled={isPending}
            label="Esemény neve"
            name="title"
            rules={{
              maxLength: 200,
              required: true,
              validate: (value) => {
                return !!value.trim();
              },
            }}
          >
            <InputText autoFocus type="text" />
          </FormField>
          <FormField
            className="col-12 mb-4 md:col-6"
            control={control}
            disabled={isPending}
            inputId
            label="Kezdés időpontja"
            name="start_datetime"
            rules={{ required: true }}
          >
            <Calendar
              mask="9999.99.99 99:99"
              showButtonBar
              showIcon
              showOnFocus={false}
              showTime
            />
          </FormField>
          <FormField
            className="col-12 mb-4 md:col-6"
            control={control}
            disabled={isPending}
            inputId
            label="Befejezés időpontja"
            name="end_datetime"
            rules={{ required: true }}
          >
            <Calendar
              mask="9999.99.99 99:99"
              showButtonBar
              showIcon
              showOnFocus={false}
              showTime
            />
          </FormField>
          <FormField
            className="col-12 mb-4 md:col-6 md:mb-0"
            control={control}
            disabled={isPending}
            icon="pi-map-marker"
            label="Helyszín"
            name="place"
            rules={{
              maxLength: 150,
              required: true,
              validate: (value) => {
                return !!value.trim();
              },
            }}
          >
            <InputText type="text" />
          </FormField>
          <FormField
            className="col-12 mb-0 md:col-6"
            control={control}
            disabled={isPending}
            inputId
            label="Típus"
            name="type"
            rules={{
              maxLength: 50,
              required: true,
              validate: (value) => {
                return !!value.trim();
              },
            }}
          >
            <Dropdown
              aria-label="Típus"
              editable
              options={requestTypeOptions}
            />
          </FormField>
          <Divider align="center" type="dashed">
            <b>Opcionális mezők</b>
          </Divider>
          {!requestId && (
            <>
              <FormField
                className="col-12 mb-0"
                control={control}
                disabled={isPending}
                label="Megjegyzések"
                name="comment"
              >
                <InputTextarea autoResize rows={isMobile ? 5 : 8} />
              </FormField>
              <Divider type="dashed" />
            </>
          )}
          <FormField
            className="col-12 mb-4 md:col-4 md:mb-0"
            control={control}
            disabled={isPending}
            inputId
            label="Felelős"
            name="responsible"
          >
            <AutoCompleteStaff />
          </FormField>
          <FormField
            className="col-12 mb-4 md:col-4 md:mb-0"
            control={control}
            disabled={isPending}
            inputId
            label="Határidő"
            name="deadline"
          >
            <Calendar
              mask="9999.99.99"
              placeholder={
                requestId ? 'Nincs változás' : 'Az esemény vége után 3 hét'
              }
              showIcon
              showOnFocus={false}
            />
          </FormField>
          <FormField
            className="col-12 mb-0 md:col-4"
            control={control}
            disabled={isPending}
            inputId
            label="Projekt"
            name="project"
          >
            <Dropdown
              filter
              optionLabel="name"
              optionValue="id"
              options={projects ?? []}
              placeholder="Nincs projekt"
              showClear
            />
          </FormField>
          <Divider align="center" type="dashed">
            <b>Felkérő</b>
          </Divider>
          <Controller
            control={control}
            disabled={isPending}
            name="requesterType"
            render={({ field }) =>
              isMobile ? (
                <div className="col-12 mb-0">
                  <Dropdown
                    {...field}
                    aria-label="Felkérő"
                    id={field.name}
                    itemTemplate={requesterTypeOptionTemplate}
                    optionLabel="text"
                    optionValue="value"
                    options={requesterTypeOptions}
                    valueTemplate={requesterTypeOptionTemplate}
                  />
                </div>
              ) : (
                <div className="col-12 mb-0">
                  <SelectButton
                    {...field}
                    allowEmpty={false}
                    aria-label="Felkérő"
                    id={field.name}
                    itemTemplate={requesterTypeOptionTemplate}
                    optionLabel="text"
                    optionValue="value"
                    options={requesterTypeOptions}
                  />
                </div>
              )
            }
          />
          {watchRequesterType === 'search' && (
            <Controller
              name="requester"
              control={control}
              render={({ field }) => (
                <div className="col-12 field mb-0 mt-4">
                  <Suspense fallback={<ProgressBar mode="indeterminate" />}>
                    <UsersDataTable
                      onSelectionChange={(e) => {
                        if (!isPending) field.onChange(e.value);
                      }}
                      selection={field.value || undefined}
                      selectionMode="single"
                    />
                  </Suspense>
                </div>
              )}
            />
          )}
          {watchRequesterType === 'new' && (
            <NewRequesterForm control={control} disabled={isPending} />
          )}
          <Divider />

          <SplitButton
            className="col-12 md:col-3 w-auto"
            disabled={isPending}
            icon="pi pi-save"
            loading={isPending}
            label="Mentés"
            model={buttonOptions}
            onClick={handleSubmit(onSubmit)}
          />
          {!requestId && (
            <div className="col-12 field-checkbox md:col-3 md:mb-0 md:mt-0 mt-3">
              <Controller
                control={control}
                disabled={isPending}
                name="createMore"
                render={({ field }) => (
                  <Checkbox
                    {...field}
                    checked={!!field.value}
                    inputId={field.name}
                    onChange={(e) => {
                      field.onChange(e.checked);
                    }}
                  />
                )}
              />
              <label htmlFor="createMore">Több létrehozása</label>
            </div>
          )}
        </div>
      </form>
      {requestId && <LastUpdatedAt lastUpdatedAt={new Date(dataUpdatedAt)} />}
    </div>
  );
};

export { RequestCreatorEditorPage as Component };
