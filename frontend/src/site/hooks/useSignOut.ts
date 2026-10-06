import { useNavigate } from 'react-router';
import { toast } from 'sonner';

import { getApiErrorMessage } from 'api/errors';
import { signOut } from 'helpers/session';

export function useSignOut() {
  const navigate = useNavigate();

  return async () => {
    try {
      await signOut();
    } catch (error) {
      toast.error('Nem sikerült kijelentkezni.', {
        description: getApiErrorMessage(error),
      });
      return;
    }
    toast.success('Sikeresen kijelentkeztél.');
    void navigate('/', { replace: true });
  };
}
