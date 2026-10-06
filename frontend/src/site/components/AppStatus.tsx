import { useEffect } from 'react';

import { toast } from 'sonner';

import { useAppUpdate } from 'hooks/useAppUpdate';
import { useOnline } from 'hooks/useOnline';

export default function AppStatus() {
  const online = useOnline();
  const { needRefresh, update } = useAppUpdate();

  useEffect(() => {
    if (!needRefresh) return;
    toast('Új verzió érhető el', {
      action: { label: 'Frissítés', onClick: () => void update() },
      description: 'Frissítsd az oldalt, hogy a legújabbat használd.',
      duration: Infinity,
      id: 'app-update',
    });
  }, [needRefresh, update]);

  if (online) return null;

  return (
    <div
      className="fixed top-[calc(5rem+env(safe-area-inset-top))] left-1/2 z-40 flex -translate-x-1/2 animate-in items-center gap-2 rounded-full bg-ink/90 px-4 py-2 text-sm whitespace-nowrap text-white shadow-lg ring-1 ring-white/15 backdrop-blur fade-in slide-in-from-top-2"
      role="status"
    >
      <span className="size-2 rounded-full bg-tally motion-safe:animate-pulse" />
      Nincs internetkapcsolat
    </div>
  );
}
