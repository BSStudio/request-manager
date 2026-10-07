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
  // Back to the page the user started from, also when it was cancelled.
  const target = `/${response?.operation ?? 'login'}`;

  useEffect(() => {
    forgetAuthorizationState();
    if (!response?.code) {
      toast.error(
        response?.operation === 'profile'
          ? 'A fiók összekapcsolása megszakadt.'
          : 'A bejelentkezés megszakadt.',
        { description: 'Próbáld újra!', id: 'oauth-redirect' },
      );
    }
  }, [response]);

  if (!response?.code) return <Navigate replace to={target} />;

  return (
    <Navigate
      replace
      state={{
        code: response.code,
        nonce: response.nonce,
        provider: response.provider,
      }}
      to={target}
    />
  );
}

export { OAuthRedirectPage as Component };
