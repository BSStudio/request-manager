import { useState } from 'react';

import { keepPreviousData, useQuery } from '@tanstack/react-query';
import { Dropdown } from 'primereact/dropdown';
import type { DropdownChangeEvent } from 'primereact/dropdown';

import { requestsListQuery } from 'admin/api/queries';
import LastUpdatedAt from 'admin/components/LastUpdatedAt/LastUpdatedAt';
import RequestsDataTable from 'admin/components/RequestsDataTable/RequestsDataTable';
import {
  Semester,
  getLatestSemester,
  getSemesters,
} from 'admin/helpers/SemesterHelper';
import { queryClient } from 'api/queryClient';

type Sort = { field: string; order: 1 | -1 };

const firstPage = { first: 0, rows: 25 };
const defaultSort: Sort = { field: 'start_datetime', order: -1 };

// The table sorts the responsible column by full name, the API by its parts.
function toOrdering({ field, order }: Sort) {
  const fields =
    field === 'responsible.full_name'
      ? ['responsible__last_name', 'responsible__first_name']
      : [field];
  return fields.map((name) => (order === -1 ? `-${name}` : name)).join(',');
}

export async function loader() {
  return queryClient.query({
    ...requestsListQuery(
      getLatestSemester(),
      1,
      firstPage.rows,
      toOrdering(defaultSort),
    ),
    staleTime: 'static',
  });
}

const RequestsListPage = () => {
  const [selectedSemester, setSelectedSemester] = useState<Semester | null>(
    getLatestSemester(),
  );
  const [{ first, rows }, setPage] = useState(firstPage);
  const [sort, setSort] = useState(defaultSort);
  const { data, dataUpdatedAt, isLoading, isPlaceholderData, refetch } =
    useQuery({
      ...requestsListQuery(
        selectedSemester,
        first / rows + 1,
        rows,
        toOrdering(sort),
      ),
      placeholderData: keepPreviousData,
    });

  return (
    <div className="p-3 sm:p-5 surface-ground">
      <div className="align-items-center flex font-medium mb-3 text-900 text-xl">
        <div>Felkérések</div>
        <Dropdown
          className="ml-2"
          filter
          onChange={(e: DropdownChangeEvent) => {
            setSelectedSemester(e.value);
            setPage({ first: 0, rows });
          }}
          options={getSemesters()}
          optionLabel="name"
          placeholder="Félév választás"
          showClear
          value={selectedSemester}
        />
      </div>
      <div className="border-round p-3 shadow-2 sm:p-4 surface-card">
        <RequestsDataTable
          first={first}
          lazy
          loading={isLoading || isPlaceholderData}
          onPage={(e) => setPage({ first: e.first, rows: e.rows })}
          onSort={(e) => {
            setSort({ field: e.sortField, order: e.sortOrder === 1 ? 1 : -1 });
            setPage({ first: 0, rows });
          }}
          requests={data?.results ?? []}
          rows={rows}
          sortField={sort.field}
          sortOrder={sort.order}
          totalRecords={data?.count ?? 0}
        />
      </div>
      <LastUpdatedAt
        lastUpdatedAt={new Date(dataUpdatedAt)}
        refetch={refetch}
      />
    </div>
  );
};

export { RequestsListPage as Component };
