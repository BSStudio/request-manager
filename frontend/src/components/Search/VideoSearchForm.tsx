import { Dispatch, SetStateAction, useState } from 'react';

import { Calendar } from 'primereact/calendar';
import { Divider } from 'primereact/divider';
import { InputMask } from 'primereact/inputmask';
import { InputText } from 'primereact/inputtext';
import { MultiSelect } from 'primereact/multiselect';
import { SplitButton } from 'primereact/splitbutton';
import { Controller, useForm } from 'react-hook-form';

import { AdminVideosListStatusEnum } from 'api/endpoints/admin-api';
import { adminApi } from 'api/http';
import { VideoAdminSearch } from 'api/models/video-admin-search';
import { VideoStatusTag } from 'components/StatusTag/StatusTag';
import { VIDEO_STATUSES } from 'components/StatusTag/statusTagConsts';
import { SearchStatusDropdownType } from 'pages/SearchPage';

interface IVideoSearchForm {
  last_aired: Date | null;
  length_max?: string;
  length_min?: string;
  request_start_datetime_after: Date | null;
  request_start_datetime_before: Date | null;
  status: SearchStatusDropdownType[] | null;
  title: string;
}

type VideoSearchFormProps = {
  setVideoSearchResults: Dispatch<SetStateAction<VideoAdminSearch[]>>;
};

const VideoSearchForm = ({ setVideoSearchResults }: VideoSearchFormProps) => {
  const defaultValues = {
    last_aired: null,
    request_start_datetime_after: null,
    request_start_datetime_before: null,
    status: null,
    title: '',
  };

  const videoStatuses = () => {
    const array: SearchStatusDropdownType[] = [];
    Object.keys(VIDEO_STATUSES).forEach((status_key) => {
      const status_num = Number(status_key);
      array.push({ ...VIDEO_STATUSES[status_num], status: status_num });
    });
    return array;
  };

  const { control, handleSubmit, reset } = useForm<IVideoSearchForm>({
    defaultValues,
  });
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const searchButtonItems = [
    {
      command: () => {
        reset();
        setVideoSearchResults([]);
      },
      icon: 'pi pi-refresh',
      label: 'Visszaállítás',
    },
  ];

  const statusTemplate = (option: SearchStatusDropdownType) => {
    return <VideoStatusTag statusNum={option.status} />;
  };

  const lengthFromString = (length: string) => {
    const [hours, minutes, seconds] = length.split(':');
    return Number(hours) * 60 * 60 + Number(minutes) * 60 + Number(seconds);
  };

  const onSubmit = async (data: IVideoSearchForm) => {
    setIsLoading(true);
    const last_aired = data.last_aired
      ? data.last_aired.toISOString().split('T')[0]
      : undefined;
    const length_max = data.length_max
      ? lengthFromString(data.length_max)
      : undefined;
    const length_min = data.length_min
      ? lengthFromString(data.length_min)
      : undefined;
    const title = data.title || undefined;
    const start_datetime_after = data.request_start_datetime_after
      ? data.request_start_datetime_after.toISOString().split('T')[0]
      : undefined;
    const start_datetime_before = data.request_start_datetime_before
      ? data.request_start_datetime_before.toISOString().split('T')[0]
      : undefined;
    const status = data.status
      ? data.status.map(({ status }) => status)
      : undefined;

    await adminApi
      .adminVideosList(
        last_aired,
        length_max,
        length_min,
        undefined,
        undefined,
        10000,
        undefined,
        start_datetime_after,
        start_datetime_before,
        title,
        status as AdminVideosListStatusEnum[],
      )
      .then((response) => {
        setVideoSearchResults(response.data.results || []);
      })
      .finally(() => {
        setIsLoading(false);
      });
  };

  return (
    <form className="formgrid grid p-fluid">
      <Controller
        control={control}
        name="title"
        render={({ field }) => (
          <div className="field col-12 mb-4 md:col-6">
            <label className="font-medium text-900" htmlFor={field.name}>
              Videó címe
            </label>
            <InputText {...field} type="text" />
          </div>
        )}
      />
      <Controller
        control={control}
        name="status"
        render={({ field }) => (
          <div className="field col-12 mb-4 md:col-6">
            <label className="font-medium text-900" htmlFor={field.name}>
              Státusz
            </label>
            <MultiSelect
              {...field}
              display="chip"
              id={field.name}
              itemTemplate={statusTemplate}
              name="status"
              onChange={(e) => field.onChange(e.value)}
              optionLabel="text"
              options={videoStatuses()}
              value={field.value}
            />
          </div>
        )}
      />
      <Controller
        control={control}
        name="length_min"
        render={({ field }) => (
          <div className="field col-6 mb-4 md:col-3">
            <label className="font-medium text-900" htmlFor={field.name}>
              Hossz (min)
            </label>
            <InputMask
              {...field}
              mask="99:99:99"
              placeholder="hh:mm:ss"
              type="text"
            />
          </div>
        )}
      />
      <Controller
        control={control}
        name="length_max"
        render={({ field }) => (
          <div className="field col-6 mb-4 md:col-3">
            <label className="font-medium text-900" htmlFor={field.name}>
              Hossz (max)
            </label>
            <InputMask
              {...field}
              mask="99:99:99"
              placeholder="hh:mm:ss"
              type="text"
            />
          </div>
        )}
      />
      <Controller
        control={control}
        name="last_aired"
        render={({ field }) => (
          <div className="field col-12 mb-4 md:col-6">
            <label className="font-medium text-900" htmlFor={field.name}>
              Utoljára adásba került
            </label>
            <Calendar {...field} mask="9999.99.99" showButtonBar showIcon />
          </div>
        )}
      />
      <Controller
        control={control}
        name="request_start_datetime_after"
        render={({ field }) => (
          <div className="field col-12 mb-4 md:col-6 md:mb-0">
            <label className="font-medium text-900" htmlFor={field.name}>
              Felkérés kezdő időpontja későbbi mint
            </label>
            <Calendar {...field} mask="9999.99.99" showButtonBar showIcon />
          </div>
        )}
      />
      <Controller
        control={control}
        name="request_start_datetime_before"
        render={({ field }) => (
          <div className="field col-12 mb-0 md:col-6">
            <label className="font-medium text-900" htmlFor={field.name}>
              Felkérés kezdő időpontja korábbi mint
            </label>
            <Calendar {...field} mask="9999.99.99" showButtonBar showIcon />
          </div>
        )}
      />
      <Divider />
      <SplitButton
        autoFocus
        className="col-6 lg:col-2 md:col-4"
        icon="pi pi-search"
        label="Keresés"
        loading={isLoading}
        model={searchButtonItems}
        onClick={handleSubmit(onSubmit)}
      />
    </form>
  );
};

export default VideoSearchForm;
