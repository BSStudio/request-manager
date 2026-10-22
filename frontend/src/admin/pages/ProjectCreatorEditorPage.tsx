import { lazy, Suspense, useEffect, useRef, useState } from 'react';

import { useMutation, useQuery } from '@tanstack/react-query';
import { isAxiosError } from 'axios';
import { Button } from 'primereact/button';
import { Checkbox } from 'primereact/checkbox';
import { ConfirmDialog, confirmDialog } from 'primereact/confirmdialog';
import { Divider } from 'primereact/divider';
import { Dropdown } from 'primereact/dropdown';
import { InputText } from 'primereact/inputtext';
import { ProgressBar } from 'primereact/progressbar';
import { SelectButton } from 'primereact/selectbutton';
import { Controller, useFieldArray, useForm, useWatch } from 'react-hook-form';
import type { Path, SubmitHandler } from 'react-hook-form';
import { useNavigate, useParams } from 'react-router';

import {
  projectCreateMutation,
  projectDeleteMutation,
  projectUpdateMutation,
} from 'admin/api/mutations';
import { projectRetrieveQuery, requestRetrieveQuery } from 'admin/api/queries';
import { queryKeys } from 'admin/api/queryKeys';
import AutoCompleteStaff from 'admin/components/AutoCompleteStaff/AutoCompleteStaff';
import FormField from 'admin/components/FormField/FormField';
import AddRequestsDialog from 'admin/components/ProjectEditor/AddRequestsDialog';
import ProjectRequestsTable from 'admin/components/ProjectEditor/ProjectRequestsTable';
import SeriesDialog from 'admin/components/ProjectEditor/SeriesDialog';
import NewRequesterForm from 'admin/components/RequestCreator/NewRequesterForm';
import { getErrorMessage } from 'admin/helpers/ErrorMessageProvider';
import { pickDirtyFields } from 'admin/helpers/pickDirtyFields';
import {
  type NewRequestRow,
  newRequestPayloads,
  nextRowTimes,
  projectSaveErrors,
  saveSummary,
} from 'admin/helpers/projectRows';
import {
  type RequesterValues,
  requesterPayload,
} from 'admin/helpers/requester';
import { requestTypeOptions } from 'admin/helpers/requestTypes';
import { showErrorToast } from 'admin/helpers/showErrorToast';
import useMobile from 'admin/hooks/useMobile';
import type { LoadErrorState } from 'admin/pages/ErrorPage';
import { useToast } from 'admin/providers/ToastProvider';
import type {
  ProjectRequest,
  RequestAdminList,
  RequestAdminRetrieve,
  UserNestedDetail,
} from 'api/models';
import { queryClient } from 'api/queryClient';
import { getName, isAdmin } from 'helpers/LocalStorageHelper';

const UsersDataTable = lazy(
  () => import('admin/components/UsersDataTable/UsersDataTable'),
);

export interface IProjectEditor extends RequesterValues {
  accepted: boolean;
  name: string;
  new_requests: NewRequestRow[];
  place: string;
  responsible: UserNestedDetail | null;
  type: string;
}

export type ExistingRow = {
  request: ProjectRequest | RequestAdminRetrieve;
  state: 'added' | 'kept' | 'removed';
};

const defaultValues: IProjectEditor = {
  accepted: false,
  name: '',
  new_requests: [],
  place: '',
  requester: null,
  requester_email: '',
  requester_first_name: '',
  requester_last_name: '',
  requester_mobile: '',
  requesterType: 'self',
  responsible: null,
  type: '',
};

const requesterTypeOptions = [
  { icon: 'pi pi-user', text: getName(), value: 'self' },
  { icon: 'pi pi-search', text: 'Felhasználó keresése', value: 'search' },
  { icon: 'pi pi-plus', text: 'Új felhasználó hozzáadása', value: 'new' },
];

const requesterTypeOptionTemplate = (option: {
  icon: string;
  text: string;
}) => {
  return (
    <>
      <i className={`${option.icon} pr-2 `}></i>
      <span className="p-button-label p-c">{option.text}</span>
    </>
  );
};

const ProjectCreatorEditorPage = () => {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const { showToast } = useToast();
  const isMobile = useMobile();

  const {
    control,
    formState: { dirtyFields },
    handleSubmit,
    reset,
    setError,
  } = useForm<IProjectEditor>({
    defaultValues,
    mode: 'onChange',
  });
  const newRows = useFieldArray({ control, name: 'new_requests' });
  const [existing, setExisting] = useState<ExistingRow[]>([]);
  const [addVisible, setAddVisible] = useState(false);
  const [seriesVisible, setSeriesVisible] = useState(false);

  const { data: project, error } = useQuery({
    ...projectRetrieveQuery(Number(projectId)),
    enabled: !!projectId,
  });
  const { isPending: isCreating, mutateAsync: createProject } = useMutation(
    projectCreateMutation(),
  );
  const { isPending: isUpdating, mutateAsync: updateProject } = useMutation(
    projectUpdateMutation(Number(projectId)),
  );
  const { isPending: isDeleting, mutateAsync: deleteProject } = useMutation(
    projectDeleteMutation(Number(projectId)),
  );
  const isPending = isCreating || isUpdating || isDeleting;

  const [name, place, type, requesterType, rows] = useWatch({
    control,
    name: ['name', 'place', 'type', 'requesterType', 'new_requests'],
  });

  // Filled once: a refetch later must not throw away what was typed since.
  const loadedProject = useRef<number | null>(null);
  useEffect(() => {
    if (!project || loadedProject.current === project.id) return;
    loadedProject.current = project.id;
    reset({
      ...defaultValues,
      name: project.name,
      responsible: project.responsible,
    });
    setExisting(
      project.requests.map((request) => ({ request, state: 'kept' })),
    );
  }, [project, reset]);

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

  const countOf = (state: ExistingRow['state']) =>
    existing.filter((row) => row.state === state).length;
  const summary = saveSummary({
    added: countOf('added'),
    created: rows.length,
    removed: countOf('removed'),
  });

  const onToggleExisting = (requestId: number) => {
    setExisting((rows) =>
      rows.flatMap((row) => {
        if (row.request.id !== requestId) return [row];
        if (row.state === 'added') return [];
        return [{ ...row, state: row.state === 'kept' ? 'removed' : 'kept' }];
      }),
    );
  };

  const onAddRow = () => {
    newRows.append({
      place: '',
      title: '',
      type: '',
      ...nextRowTimes(rows.at(-1)),
    });
  };

  const onAddSeries = (
    times: { end_datetime: Date; start_datetime: Date }[],
  ) => {
    newRows.append(
      times.map((time) => ({ place: '', title: '', type: '', ...time })),
    );
  };

  // The list has no end, type or place; a row shows them like the others.
  const onAddExisting = async (requests: RequestAdminList[]) => {
    const details = await Promise.all(
      requests.map(({ id }) => queryClient.query(requestRetrieveQuery(id))),
    );
    setExisting((rows) => [
      ...rows,
      ...details.map((request) => ({ request, state: 'added' as const })),
    ]);
  };

  const onSubmit: SubmitHandler<IProjectEditor> = async (values) => {
    // Only new requests have a requester.
    const requester = values.new_requests.length
      ? requesterPayload(values)
      : {};
    if (!requester) {
      showToast({
        detail: 'Nincs kijelölve felkérő',
        life: 3000,
        severity: 'error',
        summary: 'Hiba',
      });
      return;
    }
    const idsIn = (state: ExistingRow['state']) =>
      existing
        .filter((row) => row.state === state)
        .map((row) => row.request.id);
    const responsible = values.responsible?.id ?? null;
    const projectFields = { name: values.name, responsible };
    const payload = {
      add_requests: idsIn('added'),
      new_requests: newRequestPayloads(values.new_requests, {
        accepted: values.accepted,
        name: values.name,
        place: values.place,
        requester,
        responsible,
        type: values.type,
      }),
      remove_requests: idsIn('removed'),
    };

    try {
      await (projectId
        ? updateProject({
            ...payload,
            ...pickDirtyFields(projectFields, dirtyFields),
          })
        : createProject({ ...payload, ...projectFields }));
    } catch (error) {
      if (isAxiosError(error) && error.response?.status === 400) {
        const { fields, other } = projectSaveErrors(error.response.data);
        fields.forEach(([path, message]) =>
          setError(path as Path<IProjectEditor>, { message, type: 'backend' }),
        );
        if (other.length) {
          showToast({
            detail: other.join('\n'),
            life: 6000,
            severity: 'error',
            summary: 'Hiba',
          });
        }
        if (fields.length || other.length) return;
      }
      showErrorToast(error);
      return;
    }
    await queryClient.invalidateQueries({ queryKey: queryKeys.projects() });
    await queryClient.invalidateQueries({ queryKey: queryKeys.requests() });
    showToast({
      detail: 'Projekt mentve',
      life: 3000,
      severity: 'success',
      summary: 'Siker',
    });
    void navigate('/projects');
  };

  const onDelete = () => {
    confirmDialog({
      accept: async () => {
        try {
          await deleteProject();
        } catch (error) {
          showErrorToast(error);
          return;
        }
        // Left first: refetching the deleted project here would end in a 404.
        await navigate('/projects');
        await queryClient.invalidateQueries({ queryKey: queryKeys.projects() });
        await queryClient.invalidateQueries({ queryKey: queryKeys.requests() });
      },
      acceptClassName: 'p-button-danger',
      breakpoints: { '768px': '95vw' },
      defaultFocus: 'reject',
      header: 'Biztosan törölni akarod a projektet?',
      icon: 'pi pi-exclamation-triangle',
      message: `A(z) „${name}” projekt törlődik. A felkérései megmaradnak, csak kikerülnek a projektből.`,
      style: { width: '50vw' },
    });
  };

  return (
    <div className="p-3 sm:p-5 surface-ground">
      <ConfirmDialog />
      <div className="font-medium mb-3 text-900 text-xl">
        {projectId ? 'Projekt szerkesztése' : 'Projekt létrehozása'}
      </div>
      <form className="border-round p-3 p-fluid shadow-2 sm:p-4 surface-card">
        <div className="formgrid grid p-fluid">
          <FormField
            className="col-12 mb-4 md:col-6 md:mb-0"
            control={control}
            disabled={isPending}
            label="Projekt neve"
            name="name"
            rules={{
              maxLength: 200,
              required: true,
              validate: (value) => !!value.trim(),
            }}
          >
            <InputText autoComplete="off" autoFocus type="text" />
          </FormField>
          <FormField
            className="col-12 mb-0 md:col-6"
            control={control}
            disabled={isPending}
            inputId
            label="Felelős"
            name="responsible"
          >
            <AutoCompleteStaff />
          </FormField>
          <Divider align="center" type="dashed">
            <b>Új felkérések közös adatai</b>
          </Divider>
          <FormField
            className="col-12 mb-4 md:col-6"
            control={control}
            disabled={isPending}
            inputId
            label="Videó típusa"
            name="type"
          >
            <Dropdown
              aria-label="Videó típusa"
              editable
              options={requestTypeOptions}
            />
          </FormField>
          <FormField
            className="col-12 mb-4 md:col-6"
            control={control}
            disabled={isPending}
            icon="pi-map-marker"
            label="Helyszín"
            name="place"
          >
            <InputText type="text" />
          </FormField>
          <div className="col-12 field mb-0">
            <label className="font-medium text-900">Felkérő</label>
            <Controller
              control={control}
              disabled={isPending}
              name="requesterType"
              render={({ field }) =>
                isMobile ? (
                  <Dropdown
                    {...field}
                    aria-label="Felkérő"
                    itemTemplate={requesterTypeOptionTemplate}
                    optionLabel="text"
                    optionValue="value"
                    options={requesterTypeOptions}
                    valueTemplate={requesterTypeOptionTemplate}
                  />
                ) : (
                  <SelectButton
                    {...field}
                    allowEmpty={false}
                    aria-label="Felkérő"
                    itemTemplate={requesterTypeOptionTemplate}
                    optionLabel="text"
                    optionValue="value"
                    options={requesterTypeOptions}
                  />
                )
              }
            />
          </div>
          {requesterType === 'search' && (
            <Controller
              control={control}
              name="requester"
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
          {requesterType === 'new' && (
            <NewRequesterForm control={control} disabled={isPending} />
          )}
          {isAdmin() && (
            <div className="col-12 field-checkbox mb-0 mt-4">
              <Controller
                control={control}
                disabled={isPending}
                name="accepted"
                render={({ field }) => (
                  <Checkbox
                    {...field}
                    checked={field.value}
                    inputId={field.name}
                    onChange={(e) => field.onChange(e.checked)}
                  />
                )}
              />
              <label htmlFor="accepted">Új felkérések elfogadása</label>
            </div>
          )}
          <Divider align="center" type="dashed">
            <b>Felkérések</b>
          </Divider>
          <div className="col-12">
            <ProjectRequestsTable
              control={control}
              disabled={isPending}
              existing={existing}
              newRows={newRows.fields}
              onDropNew={newRows.remove}
              onToggleExisting={onToggleExisting}
              placeholders={{ place, title: name, type }}
            />
            <div className="flex flex-wrap gap-2 mt-3">
              <Button
                aria-label="Új felkérés"
                disabled={isPending}
                icon="pi pi-plus"
                onClick={onAddRow}
                tooltip="Új felkérés"
                type="button"
              />
              <Button
                className="w-auto"
                disabled={isPending}
                icon="pi pi-calendar-plus"
                label="Ismétlődő alkalmak…"
                onClick={() => setSeriesVisible(true)}
                outlined
                type="button"
              />
              <Button
                className="w-auto"
                disabled={isPending}
                icon="pi pi-link"
                label="Meglévő felkérések hozzáadása…"
                onClick={() => setAddVisible(true)}
                outlined
                type="button"
              />
            </div>
            <SeriesDialog
              onAdd={onAddSeries}
              onHide={() => setSeriesVisible(false)}
              visible={seriesVisible}
            />
            <AddRequestsDialog
              excludedIds={existing.map(({ request }) => request.id)}
              onAdd={onAddExisting}
              onHide={() => setAddVisible(false)}
              visible={addVisible}
            />
          </div>
          <Divider />
          <div className="align-items-center col-12 flex flex-wrap gap-2">
            <Button
              className="w-auto"
              disabled={isPending}
              icon="pi pi-save"
              label="Mentés"
              loading={isCreating || isUpdating}
              onClick={handleSubmit(onSubmit)}
              type="button"
            />
            <Button
              className="w-auto"
              disabled={isPending}
              label="Mégsem"
              onClick={() => void navigate('/projects')}
              text
              type="button"
            />
            {summary && <span className="text-600">{summary}</span>}
            {projectId && (
              <Button
                className="ml-auto w-auto"
                disabled={isPending}
                icon="pi pi-trash"
                label="Projekt törlése"
                onClick={onDelete}
                outlined
                severity="danger"
                type="button"
              />
            )}
          </div>
        </div>
      </form>
    </div>
  );
};

export { ProjectCreatorEditorPage as Component };
