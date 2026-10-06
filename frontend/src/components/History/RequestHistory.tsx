import { useQuery } from '@tanstack/react-query';
import { ProgressBar } from 'primereact/progressbar';
import { Skeleton } from 'primereact/skeleton';

import { requestHistoryListQuery, usersListQuery } from 'api/queries';
import { RequestStatusTag } from 'components/StatusTag/StatusTag';
import User from 'components/User/User';
import {
  dateTimeToLocaleString,
  dateToLocaleString,
} from 'helpers/DateToLocaleStringCoverters';

import HistoryComponent, { getHistory } from './History';

type RequestHistoryProps = {
  requestId: number;
};

const RequestFieldNames: Record<string, string> = {
  additional_data: 'Egyéb adatok',
  created: 'Létrehozás ideje',
  deadline: 'Határidő',
  end_datetime: 'Esemény vége',
  place: 'Helyszín',
  requested_by: 'Beküldő',
  requester: 'Felkérő',
  responsible: 'Felelős',
  start_datetime: 'Esemény kezdése',
  status: 'Státusz',
  title: 'Esemény neve',
  type: 'Típus',
};

const RequestHistory = ({ requestId }: RequestHistoryProps) => {
  const { data = [], isLoading } = useQuery({
    ...requestHistoryListQuery(requestId),
    select: getHistory,
  });
  const { data: users } = useQuery(usersListQuery());

  const getFieldName = (name: string) => {
    return RequestFieldNames[name];
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
    if (['created', 'end_datetime', 'start_datetime'].includes(name)) {
      return dateTimeToLocaleString(new Date(value));
    }
    if (name === 'deadline') {
      return dateToLocaleString(new Date(value));
    }
    if (['requested_by', 'requester', 'responsible'].includes(name)) {
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
      return <RequestStatusTag statusNum={Number(value)} />;
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

export default RequestHistory;
