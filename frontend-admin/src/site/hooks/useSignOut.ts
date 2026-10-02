import { useNavigate } from 'react-router';
import { toast } from 'sonner';

import { signOut } from 'site/lib/session';

export function useSignOut() {
  const navigate = useNavigate();

  return async () => {
    await signOut().finally(() => {
      toast.success('Sikeresen kijelentkeztél.');
      void navigate('/', { replace: true });
    });
  };
}
