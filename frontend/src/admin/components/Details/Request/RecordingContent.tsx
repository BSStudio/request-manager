import { Button } from 'primereact/button';
import { ButtonGroup } from 'primereact/buttongroup';
import { Dropdown } from 'primereact/dropdown';
import { Tag } from 'primereact/tag';
import { Controller } from 'react-hook-form';
import type { Control } from 'react-hook-form';

import { useToast } from 'admin/providers/ToastProvider';
import { RequestAdditionalDataRecordingType } from 'admin/types/additionalDataTypes';

type RequestAdditionalDataRecordingFormType = {
  control: Control<RequestAdditionalDataRecordingType>;
  loading: boolean;
  recommendedPath: string;
};

type RecordingContentProps = RequestAdditionalDataRecordingType &
  RequestAdditionalDataRecordingFormType & {
    editing: boolean;
  };

type RecordingContentButtonsEditingProps = {
  editOnCancel: React.MouseEventHandler<HTMLButtonElement>;
  editOnSave: React.MouseEventHandler<HTMLButtonElement>;
  loading: boolean;
};

type RecordingContentButtonsNonEditingProps = {
  editOnClick: React.MouseEventHandler<HTMLButtonElement>;
  recordingPath: string | undefined;
};

type RecordingContentButtonsProps = RecordingContentButtonsEditingProps &
  RecordingContentButtonsNonEditingProps & {
    editing: boolean;
  };

const RecordingContentEditing = ({
  control,
  loading,
  recommendedPath,
}: RequestAdditionalDataRecordingFormType) => {
  return (
    <form>
      <div className="align-items-center flex">
        <Controller
          control={control}
          disabled={loading}
          name="path"
          render={({ field }) => (
            <Dropdown
              {...field}
              aria-label="Elérési út"
              className="flex-grow-1"
              editable
              onChange={(e) => {
                field.onChange(e.value);
              }}
              options={[recommendedPath]}
              placeholder="Elérési út"
            />
          )}
        />
      </div>
      <div className="align-items-center flex flex-wrap">
        <Controller
          control={control}
          name="copied_to_gdrive"
          render={({ field }) => (
            <button
              className="bg-transparent border-none cursor-pointer p-0 mr-2 mt-2"
              disabled={loading}
              onClick={() => field.onChange(!field.value)}
              type="button"
            >
              <Tag
                icon="pi pi-cloud-upload"
                pt={{ icon: { 'aria-hidden': true } }}
                severity={field.value ? 'success' : 'warning'}
                value={
                  field.value
                    ? 'Felmásolva Google Driveba'
                    : 'Nincsenek felmásolva Google Driveba'
                }
              />
            </button>
          )}
        />
        <Controller
          control={control}
          name="removed"
          render={({ field }) => (
            <button
              className="bg-transparent border-none cursor-pointer p-0 mt-2"
              disabled={loading}
              onClick={() => field.onChange(!field.value)}
              type="button"
            >
              <Tag
                icon="pi pi-trash"
                pt={{ icon: { 'aria-hidden': true } }}
                severity={field.value ? 'success' : 'warning'}
                value={field.value ? 'Törölve' : 'Nincsenek törölve'}
              />
            </button>
          )}
        />
      </div>
    </form>
  );
};

const RecordingContentNonEditing = ({
  copied_to_gdrive,
  path,
  removed,
}: RequestAdditionalDataRecordingType) => {
  return (
    <div>
      <div className="align-items-center flex mb-2">
        <span>{path || ''}</span>
      </div>
      <div className="align-items-center flex flex-wrap">
        <Tag
          className="mr-2 mt-1"
          icon="pi pi-cloud-upload"
          severity={copied_to_gdrive ? 'success' : 'warning'}
          value={
            copied_to_gdrive
              ? 'Felmásolva Google Driveba'
              : 'Nincsenek felmásolva Google Driveba'
          }
        />
        <Tag
          className="mt-1"
          icon="pi pi-trash"
          severity={removed ? 'success' : 'warning'}
          value={removed ? 'Törölve' : 'Nincsenek törölve'}
        />
      </div>
    </div>
  );
};

export const RecordingContent = ({
  control,
  copied_to_gdrive,
  editing,
  loading,
  path,
  recommendedPath,
  removed,
}: RecordingContentProps) => {
  return editing ? (
    <RecordingContentEditing
      control={control}
      loading={loading}
      recommendedPath={recommendedPath}
    />
  ) : path ? (
    <RecordingContentNonEditing
      copied_to_gdrive={copied_to_gdrive}
      path={path}
      removed={removed}
    />
  ) : (
    <></>
  );
};

const RecordingContentButtonsEditing = ({
  editOnCancel,
  editOnSave,
  loading,
}: RecordingContentButtonsEditingProps) => {
  return (
    <ButtonGroup
      pt={{
        root: {
          className: 'flex flex-no-wrap justify-content-end sm:flex-wrap',
        },
      }}
    >
      <Button
        className="p-button-sm p-button-text pl-1 pr-2 py-0"
        disabled={loading}
        icon="pi pi-check"
        label="Mentés"
        onClick={editOnSave}
      />
      <Button
        className="p-button-sm p-button-text pl-2 pr-1 py-0"
        disabled={loading}
        icon="pi pi-times"
        label="Mégsem"
        onClick={editOnCancel}
      />
    </ButtonGroup>
  );
};

const RecordingContentButtonsNonEditing = ({
  editOnClick,
  recordingPath,
}: RecordingContentButtonsNonEditingProps) => {
  const _recordingPath = recordingPath || '';
  const { showToast } = useToast();

  return (
    <ButtonGroup
      pt={{
        root: {
          className: 'flex flex-no-wrap justify-content-end sm:flex-wrap',
        },
      }}
    >
      <Button
        className="p-button-sm p-button-text pl-1 pr-2 py-0"
        icon="pi pi-pencil"
        label="Szerkesztés"
        onClick={editOnClick}
      />
      <Button
        className="p-button-sm p-button-text pl-2 pr-1 py-0"
        disabled={_recordingPath.length == 0}
        icon="pi pi-folder-open"
        label="Másolás"
        onClick={() => {
          showToast({
            detail: 'Elérési út a vágólapra másolva',
            life: 3000,
            severity: 'info',
            summary: 'Információ',
          });
          void navigator.clipboard.writeText(_recordingPath);
        }}
      />
    </ButtonGroup>
  );
};

export const RecordingContentButtons = ({
  editing,
  editOnCancel,
  editOnClick,
  editOnSave,
  loading,
  recordingPath,
}: RecordingContentButtonsProps) => {
  return editing ? (
    <RecordingContentButtonsEditing
      editOnCancel={editOnCancel}
      editOnSave={editOnSave}
      loading={loading}
    />
  ) : (
    <RecordingContentButtonsNonEditing
      editOnClick={editOnClick}
      recordingPath={recordingPath}
    />
  );
};
