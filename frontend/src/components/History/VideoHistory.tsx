import { useQuery } from '@tanstack/react-query';
import { ProgressBar } from 'primereact/progressbar';
import { Skeleton } from 'primereact/skeleton';

import { requestVideoHistoryListQuery, usersListQuery } from 'api/queries';
import { VideoStatusTag } from 'components/StatusTag/StatusTag';
import User from 'components/User/User';

import HistoryComponent, { getHistory } from './History';

type VideoHistoryProps = {
  requestId: number;
  videoId: number;
};

const VideoFieldNames: Record<string, string> = {
  additional_data: 'Egyéb adatok',
  editor: 'Vágó',
  status: 'Státusz',
  title: 'Videó címe',
};

const VideoHistory = ({ requestId, videoId }: VideoHistoryProps) => {
  const { data = [], isLoading } = useQuery({
    ...requestVideoHistoryListQuery(requestId, videoId),
    select: getHistory,
  });
  const { data: users } = useQuery(usersListQuery());

  const getFieldName = (name: string) => {
    return VideoFieldNames[name];
  };

  const getFieldValue = (name: string, value: string) => {
    if (!value) {
      return 'Nincs';
    }
    if (name === 'additional_data') {
      const obj = JSON.parse(
        value
          .replace(/'/g, '"')
          .replaceAll('True', 'true')
          .replaceAll('False', 'false')
          .replaceAll('None', 'null'),
      );
      return JSON.stringify(obj, null, 2);
    }
    if (name === 'editor') {
      const user = users?.find((user) => user.id === Number(value));

      if (!user)
        return (
          <div className="align-items-center flex flex-row gap-2">
            <Skeleton shape="circle" size="32px" />
            <Skeleton width="8rem" />
          </div>
        );
      return <User name={user.full_name} imageUrl={user.avatar_url} />;
    }
    if (name === 'status') {
      return <VideoStatusTag statusNum={Number(value)} />;
    }
    return value;
  };

  if (isLoading) {
    return <ProgressBar mode="indeterminate" />;
  }

  if (data.length) {
    return (
      <HistoryComponent
        history={data}
        getFieldName={getFieldName}
        getFieldValue={getFieldValue}
      />
    );
  }

  return <p>Nem történt még módosítás.</p>;
};

export default VideoHistory;
