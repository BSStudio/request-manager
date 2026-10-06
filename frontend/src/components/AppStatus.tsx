import { useEffect } from 'react';

import { Button } from 'primereact/button';
import { Tag } from 'primereact/tag';

import { useAppUpdate } from 'hooks/useAppUpdate';
import { useOnline } from 'hooks/useOnline';
import { useToast } from 'providers/ToastProvider';

const AppStatus = () => {
  const online = useOnline();
  const { needRefresh, update } = useAppUpdate();
  const { showToast } = useToast();

  useEffect(() => {
    if (!needRefresh) return;
    showToast({
      content: (
        <div className="flex flex-column gap-3 w-full">
          <div>
            <div className="font-bold">Új verzió érhető el</div>
            <div className="mt-1">
              Frissítsd az oldalt, hogy a legújabbat használd.
            </div>
          </div>
          <Button
            label="Frissítés"
            onClick={() => void update()}
            size="small"
          />
        </div>
      ),
      severity: 'info',
      sticky: true,
    });
  }, [needRefresh, showToast, update]);

  if (online) return null;

  return (
    <div
      className="bottom-0 fixed left-50 mb-4 z-5"
      role="status"
      style={{ transform: 'translateX(-50%)' }}
    >
      <Tag
        className="px-3 py-2 shadow-3"
        icon="pi pi-wifi"
        rounded
        severity="danger"
        value="Nincs internetkapcsolat"
      />
    </div>
  );
};

export default AppStatus;
