import { useState } from 'react';

import { useQuery } from '@tanstack/react-query';
import type { AutoCompleteChangeEvent } from 'primereact/autocomplete';
import { ConfirmDialog } from 'primereact/confirmdialog';
import { Dropdown } from 'primereact/dropdown';
import { MultiSelect } from 'primereact/multiselect';
import type { MultiSelectChangeEvent } from 'primereact/multiselect';

import { StatusEnum } from 'api/models/status-enum';
import { UserAdminList } from 'api/models/user-admin-list';
import { todosListQuery } from 'api/queries';
import AutoCompleteStaffMultiple from 'components/AutoCompleteStaff/AutoCompleteStaffMultiple';
import LastUpdatedAt from 'components/LastUpdatedAt/LastUpdatedAt';
import { TodoStatusTag } from 'components/StatusTag/StatusTag';
import { TODO_STATUSES } from 'components/StatusTag/statusTagConsts';
import { StatusStyle } from 'components/StatusTag/StatusTagTypes';
import Todos from 'components/Todos/Todos';
import { queryClient } from 'router';

export async function loader() {
  return queryClient.query({
    ...todosListQuery([], '-created', [1]),
    staleTime: 'static',
  });
}

const TodosPage = () => {
  const [ordering, setOrdering] = useState<string>('-created');
  const [selectedAssignees, setSelectedAssignees] = useState<UserAdminList[]>(
    [],
  );
  const [selectedStatuses, setSelectedStatuses] = useState<number[]>([1]);

  const { data, dataUpdatedAt, isLoading, refetch } = useQuery(
    todosListQuery(
      selectedAssignees.map((assignee) => assignee.id).sort(),
      ordering,
      selectedStatuses.sort(),
    ),
  );

  const orderingOptions = [
    { name: 'Legújabb', value: '-created' },
    { name: 'Legrégebbi', value: 'created' },
    { name: 'Státusz növekvő', value: 'status' },
    { name: 'Státusz csökkenő', value: '-status' },
  ];

  const statusTemplate = (option: StatusStyle & { value: number }) => {
    if (!option) return;
    return <TodoStatusTag className="text-xs" statusNum={option.value} />;
  };

  return (
    <>
      <ConfirmDialog />
      <div className="p-3 sm:p-5 surface-ground">
        <div className="align-items-center flex justify-content-between mb-3">
          <div className="align-items-center flex flex-wrap font-medium gap-1 text-900 text-xl">
            <div>Feladatok</div>
            <MultiSelect
              display="chip"
              itemTemplate={statusTemplate}
              onChange={(e: MultiSelectChangeEvent) =>
                setSelectedStatuses(e.value)
              }
              optionLabel="text"
              options={Object.values(StatusEnum).map((status) =>
                Object.assign({}, { value: status }, TODO_STATUSES[status]),
              )}
              placeholder="Státusz"
              value={selectedStatuses}
            />
            <AutoCompleteStaffMultiple
              placeholder="Felelősök"
              onChange={(e: AutoCompleteChangeEvent) =>
                setSelectedAssignees(e.value)
              }
              value={selectedAssignees}
            />
          </div>
          <Dropdown
            onChange={(e) => {
              setOrdering(e.value);
            }}
            optionLabel="name"
            options={orderingOptions}
            value={ordering}
          />
        </div>
        <div className="border-round p-3 shadow-2 sm:p-4 surface-card">
          <Todos data={data} loading={isLoading} />
        </div>
        <LastUpdatedAt
          lastUpdatedAt={new Date(dataUpdatedAt)}
          refetch={refetch}
        />
      </div>
    </>
  );
};

export { TodosPage as Component };
