import { useQuery } from '@tanstack/react-query';
import { parseISO } from 'date-fns';
import { ProgressBar } from 'primereact/progressbar';
import { Skeleton } from 'primereact/skeleton';

import {
  projectsListQuery,
  requestHistoryListQuery,
  usersListQuery,
} from 'admin/api/queries';
import { RequestStatusTag } from 'admin/components/StatusTag/StatusTag';
import User from 'admin/components/User/User';
import {
  dateTimeToLocaleString,
  dateToLocaleString,
} from 'admin/helpers/DateToLocaleStringCoverters';
import { formatJson } from 'admin/helpers/formatJson';

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
  project: 'Projekt',
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
  const { data: projects } = useQuery(projectsListQuery());

  const getFieldName = (name: string) => {
    return RequestFieldNames[name];
  };

  const getFieldValue = (name: string, value: string) => {
    if (!value) {
      return 'Nincs';
    }
    if (name === 'additional_data') {
      return formatJson(value);
    }
    if (['created', 'end_datetime', 'start_datetime'].includes(name)) {
      return dateTimeToLocaleString(parseISO(value));
    }
    if (name === 'deadline') {
      return dateToLocaleString(parseISO(value));
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
    if (name === 'project') {
      // A deleted project is no longer in the list.
      return (
        projects?.find((project) => project.id === Number(value))?.name ?? value
      );
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
