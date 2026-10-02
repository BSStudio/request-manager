/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_AUTHSCH_CLIENT_ID: string;
  readonly VITE_BSS_CLIENT_ID: string;
  readonly VITE_GOOGLE_CLIENT_ID: string;
  readonly VITE_MICROSOFT_CLIENT_ID: string;
  readonly VITE_SENTRY_URL?: string;
  readonly VITE_SENTRY_URL_ADMIN?: string;
  readonly VITE_TURNSTILE_SITE_KEY: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
