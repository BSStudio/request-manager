import { useState } from 'react';

import { useQuery } from '@tanstack/react-query';
import { Button } from 'primereact/button';
import { Checkbox } from 'primereact/checkbox';
import { Dialog } from 'primereact/dialog';
import { IconField } from 'primereact/iconfield';
import { InputIcon } from 'primereact/inputicon';
import { InputText } from 'primereact/inputtext';
import { ProgressBar } from 'primereact/progressbar';

import { requestsWithoutProjectQuery } from 'admin/api/queries';
import { RequestStatusTag } from 'admin/components/StatusTag/StatusTag';
import { dateToLocaleString } from 'admin/helpers/DateToLocaleStringCoverters';
import { showErrorToast } from 'admin/helpers/showErrorToast';
import type { RequestAdminList } from 'api/models';

type AddRequestsDialogProps = {
  excludedIds: number[];
  onAdd: (requests: RequestAdminList[]) => Promise<void>;
  onHide: () => void;
  visible: boolean;
};

const AddRequestsDialog = ({
  excludedIds,
  onAdd,
  onHide,
  visible,
}: AddRequestsDialogProps) => {
  const [search, setSearch] = useState('');
  const [picked, setPicked] = useState<RequestAdminList[]>([]);
  const [isAdding, setIsAdding] = useState(false);
  const query = requestsWithoutProjectQuery(search);
  const { data, isFetching } = useQuery(query);
  const results = (data ?? []).filter(
    (request) => !excludedIds.includes(request.id),
  );

  const close = () => {
    setSearch('');
    setPicked([]);
    onHide();
  };

  const toggle = (request: RequestAdminList, checked: boolean) => {
    setPicked((picked) =>
      checked
        ? [...picked, request]
        : picked.filter(({ id }) => id !== request.id),
    );
  };

  const footer = (
    <div>
      <Button
        disabled={isAdding}
        label="Mégsem"
        onClick={close}
        text
        type="button"
      />
      <Button
        disabled={!picked.length}
        label="Hozzáadás"
        loading={isAdding}
        onClick={async () => {
          setIsAdding(true);
          try {
            await onAdd(picked);
            close();
          } catch (error) {
            showErrorToast(error);
          } finally {
            setIsAdding(false);
          }
        }}
        type="button"
      />
    </div>
  );

  return (
    <Dialog
      breakpoints={{ '768px': '95vw' }}
      footer={footer}
      header="Meglévő felkérések hozzáadása"
      onHide={close}
      style={{ width: '40rem' }}
      visible={visible}
    >
      <IconField className="mb-3" iconPosition="left">
        <InputIcon className="pi pi-search" />
        <InputText
          autoFocus
          className="w-full"
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Keresés a felkérések címében"
          value={search}
        />
      </IconField>
      {isFetching && <ProgressBar mode="indeterminate" />}
      {query.enabled && !isFetching && !results.length && (
        <p className="text-600">
          Nincs projekt nélküli felkérés ezzel a címmel.
        </p>
      )}
      {results.map((request) => {
        const inputId = `add-request-${request.id}`;
        return (
          <div
            className="align-items-center border-bottom-1 flex gap-2 py-2 surface-border"
            key={request.id}
          >
            <Checkbox
              checked={picked.some(({ id }) => id === request.id)}
              inputId={inputId}
              onChange={(e) => toggle(request, !!e.checked)}
            />
            <label className="flex-grow-1" htmlFor={inputId}>
              {request.title}
            </label>
            <span className="text-600">
              {dateToLocaleString(new Date(request.start_datetime), true)}
            </span>
            <RequestStatusTag
              modified={request.status_by_admin}
              statusNum={request.status}
            />
          </div>
        );
      })}
    </Dialog>
  );
};

export default AddRequestsDialog;
