import { useEffect, useState } from 'react';

import { Navigate, useLocation } from 'react-router';
import { toast } from 'sonner';

import {
  forgetAuthorizationState,
  readAuthorizationResponse,
} from 'site/lib/oauth';

function OAuthRedirectPage() {
  const location = useLocation();
  const [response] = useState(() => readAuthorizationResponse(location.search));

  useEffect(() => {
    forgetAuthorizationState();
    if (!response) {
      toast.error('A bejelentkezés megszakadt.', {
        description: 'Próbáld újra!',
        id: 'oauth-redirect',
      });
    }
  }, [response]);

  if (!response) return <Navigate replace to="/login" />;

  return (
    <Navigate
      replace
      state={{ code: response.code, provider: response.provider }}
      to={`/${response.operation}`}
    />
  );
}

export { OAuthRedirectPage as Component };
