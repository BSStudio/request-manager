export type OAuthProvider =
  'authsch' | 'bss-login' | 'google-oauth2' | 'microsoft-graph';

export type OAuthOperation = 'login' | 'profile';

type OAuthState = {
  hashedNonce: string;
  operation: OAuthOperation;
  provider: OAuthProvider;
};

type StoredNonce = { hashedNonce: string; nonce: string };

const STATE_KEY = 'oauth-state';

// Registered at the providers, so the path must not change.
const redirectUri = `${window.location.origin}/redirect`;

const providers: Record<
  OAuthProvider,
  { params: Record<string, string>; url: string }
> = {
  authsch: {
    params: {
      client_id: import.meta.env.VITE_AUTHSCH_CLIENT_ID,
      scope: 'directory.sch.bme.hu:sAMAccountName email openid phone profile',
    },
    url: 'https://auth.sch.bme.hu/site/login',
  },
  'bss-login': {
    params: {
      client_id: import.meta.env.VITE_BSS_CLIENT_ID,
      redirect_uri: redirectUri,
      scope: 'email mobile openid profile',
    },
    url: 'https://login.bsstudio.hu/application/o/authorize/',
  },
  'google-oauth2': {
    params: {
      client_id: import.meta.env.VITE_GOOGLE_CLIENT_ID,
      include_granted_scopes: 'true',
      redirect_uri: redirectUri,
      scope: [
        'https://www.googleapis.com/auth/userinfo.email',
        'https://www.googleapis.com/auth/userinfo.profile',
        'https://www.googleapis.com/auth/user.phonenumbers.read',
      ].join(' '),
    },
    url: 'https://accounts.google.com/o/oauth2/v2/auth',
  },
  'microsoft-graph': {
    params: {
      client_id: import.meta.env.VITE_MICROSOFT_CLIENT_ID,
      redirect_uri: redirectUri,
      response_mode: 'query',
      scope: 'https://graph.microsoft.com/.default',
    },
    url: 'https://login.microsoftonline.com/common/oauth2/v2.0/authorize',
  },
};

async function sha256(text: string) {
  const digest = await crypto.subtle.digest(
    'SHA-256',
    new TextEncoder().encode(text),
  );
  return Array.from(new Uint8Array(digest), (byte) =>
    byte.toString(16).padStart(2, '0'),
  ).join('');
}

// URLs only ever carry the nonce's hash, the nonce itself goes to the backend
// with the code. So a leaked redirect URL is not enough to redeem the code.
export async function getAuthorizationUrl(
  provider: OAuthProvider,
  operation: OAuthOperation,
) {
  const nonce = crypto.randomUUID();
  const hashedNonce = await sha256(nonce);
  const stored: StoredNonce = { hashedNonce, nonce };
  localStorage.setItem(STATE_KEY, JSON.stringify(stored));

  const state: OAuthState = { hashedNonce, operation, provider };
  const { params, url } = providers[provider];
  const query = new URLSearchParams({
    ...params,
    nonce: hashedNonce,
    response_type: 'code',
    state: btoa(JSON.stringify(state)),
  });
  return `${url}?${query}`;
}

// Only accepts the state if it carries this browser's hashed nonce, so a link
// with someone else's code cannot log the user into their account. The code is
// missing when the user cancelled at the provider.
export function readAuthorizationResponse(search: string) {
  const params = new URLSearchParams(search);

  try {
    const { hashedNonce, nonce } = JSON.parse(
      localStorage.getItem(STATE_KEY) ?? '',
    ) as StoredNonce;
    const state = JSON.parse(atob(params.get('state') ?? '')) as OAuthState;
    if (
      hashedNonce &&
      state.hashedNonce === hashedNonce &&
      state.provider in providers &&
      ['login', 'profile'].includes(state.operation)
    ) {
      return {
        code: params.get('code'),
        nonce,
        operation: state.operation,
        provider: state.provider,
      };
    }
  } catch {
    // Malformed state, handled like a missing one.
  }
  return null;
}

export function forgetAuthorizationState() {
  localStorage.removeItem(STATE_KEY);
}
