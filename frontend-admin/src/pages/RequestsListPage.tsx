import { useState } from 'react';

import { useQuery } from '@tanstack/react-query';
import { Dropdown } from 'primereact/dropdown';
import type { DropdownChangeEvent } from 'primereact/dropdown';

import { requestsListQuery } from 'api/queries';
import LastUpdatedAt from 'components/LastUpdatedAt/LastUpdatedAt';
import RequestsDataTable from 'components/RequestsDataTable/RequestsDataTable';
import {
  Semester,
  getLatestSemester,
  getSemesters,
} from 'helpers/SemesterHelper';
import { queryClient } from 'router';

export async function loader() {
  return queryClient.query({
    ...requestsListQuery(getLatestSemester()),
    staleTime: 'static',
  });
}

const RequestsListPage = () => {
  const [selectedSemester, setSelectedSemester] = useState<Semester | null>(
    getLatestSemester(),
  );
  const { data, dataUpdatedAt, isLoading, refetch } = useQuery(
    requestsListQuery(selectedSemester),
  );

  return (
    <div className="p-3 sm:p-5 surface-ground">
      <div className="align-items-center flex font-medium mb-3 text-900 text-xl">
        <div>Felkérések</div>
        <Dropdown
          className="ml-2"
          filter
          onChange={(e: DropdownChangeEvent) => setSelectedSemester(e.value)}
          options={getSemesters()}
          optionLabel="name"
          placeholder="Félév választás"
          showClear
          value={selectedSemester}
        />
      </div>
      <div className="border-round p-3 shadow-2 sm:p-4 surface-card">
        <RequestsDataTable loading={isLoading} requests={data ?? []} />
      </div>
      <LastUpdatedAt
        lastUpdatedAt={new Date(dataUpdatedAt)}
        refetch={refetch}
      />
    </div>
  );
};

export { RequestsListPage as Component };
