# Frontend

The public site where users submit and follow their requests, and the admin dashboard where staff manage video requests, crew, comments and ratings.

`index.html` serves both apps and [`src/main.tsx`](src/main.tsx) loads one of them based on the path:

| Path       | Source       | UI                                 |
| ---------- | ------------ | ---------------------------------- |
| `/admin/*` | `src/admin/` | PrimeReact, PrimeFlex              |
| Other      | `src/site/`  | Tailwind CSS, shadcn/ui (Radix UI) |

They share the API client and helpers but never run on the same page, because PrimeFlex and Tailwind CSS use the same class names. Links between the two have to reload the page (a plain `<a href>`, not a router `Link`).

**Stack:** React · TypeScript · Vite · React Router · TanStack Query · Sentry

## Setup

Requires Node.js (version pinned in [`.nvmrc`](.nvmrc); run `nvm use` to switch), pnpm (run `corepack enable` to activate the version pinned in `package.json`) and a running [backend](../backend/README.md).

```bash
cd frontend
pnpm install
cp .env.sample .env     # then edit it (see below)
pnpm start
```

The dev server runs at <https://localhost:5173> and the admin dashboard at <https://localhost:5173/admin>. It uses a self-signed certificate (via `@vitejs/plugin-basic-ssl`), so accept the browser warning on first load.

### Environment

Configuration is read from `frontend/.env`. Start from [`.env.sample`](.env.sample). Variables prefixed with `VITE_` are built into the app, the rest only configure the dev server. Production builds, the Docker image included, take the `VITE_` values from the committed [`.env.production`](.env.production); for a local production build with other values, override them in `.env.production.local`.

Builds also read two Sentry variables, which the Docker workflow sets: `SENTRY_RELEASE` is the release the app reports (the commit hash of the checkout when unset), and with `SENTRY_AUTH_TOKEN` the build uploads its source maps to Sentry and fails if the upload does. The source maps stay in `build/` for `pnpm analyze`; the Docker image leaves them out.

The app calls the API on its own origin, because the login is a session cookie. In production Django serves both, in development the dev server proxies `/api` to `BACKEND_URL` (default `http://localhost:8000`).

## UI components

The site's components in `src/site/components/ui/` come from [shadcn/ui](https://ui.shadcn.com/) and are configured in [`components.json`](components.json). Add new ones with:

```bash
pnpm dlx shadcn@latest add <component>
```

Review what the CLI changes: it adds packages with caret ranges (pin them) and may pull in ones the site does not use, such as `next-themes` for the toaster.

## API client

The TypeScript API client in `src/api/` is **generated** from the backend's OpenAPI schema (`../backend/schema.yaml`) with [`openapi-generator`](https://openapi-generator.tech/) (`typescript-axios`). Regenerate it whenever the schema changes:

```bash
pnpm generate-client
```

> Requires a Java runtime (used by openapi-generator) and an up-to-date `backend/schema.yaml` — see the [backend README](../backend/README.md#openapi-schema).

## Scripts

| Script                     | Description                                                   |
| -------------------------- | ------------------------------------------------------------- |
| `pnpm start`               | Start the Vite dev server (HTTPS, port 5173).                 |
| `pnpm start:network`       | Same, exposed on the local network (`--host`).                |
| `pnpm build`               | Type-check (`tsc --noEmit`) and build into `build/`.          |
| `pnpm preview`             | Serve the production build locally.                           |
| `pnpm lint`                | Run ESLint and type-check the end-to-end tests.               |
| `pnpm lint:fix`            | Run ESLint with autofix.                                      |
| `pnpm test`                | Run the unit tests with Vitest, rerunning them on changes.    |
| `pnpm e2e`                 | Run the end-to-end tests with Playwright (see below).         |
| `pnpm e2e:ui`              | Same, in Playwright's UI mode.                                |
| `pnpm format`              | Format sources with Prettier.                                 |
| `pnpm generate-client`     | Regenerate the API client from the backend schema.            |
| `pnpm generate-pwa-assets` | Regenerate the app icons in `public/` from `public/icon.svg`. |
| `pnpm analyze`             | Inspect the bundle with source-map-explorer.                  |

## Tests

Unit tests sit next to the code they test as `*.test.ts` and run in jsdom. `pnpm test run` runs them once; `pnpm test run --coverage` also writes a coverage report to `coverage/`.

## End-to-end tests

End-to-end tests in `e2e/` run the app in Chromium with Playwright. `pnpm e2e` builds the app with `.env.e2e`, then starts Django with `core.settings.e2e`, which recreates the `request_manager_e2e` database with the test data, writes a login for every test user and serves the build on port 8010. Postgres has to run, as for development; Redis is not needed.

Download Chromium once with `pnpm exec playwright install chromium`. Tests log in by loading a login file, `test.use({ storageState: loginAs('minta.anna') })`, and can only reach localhost and Cloudflare's Turnstile. Only one run can go at a time, because the port and the database are fixed. A run leaves its own build in `build/`, so run `pnpm build` again before `pnpm preview` or before Django serves the build.

## Code style

Formatting and linting (Prettier + ESLint) are enforced by pre-commit. Install the hooks once from the repository root with `pre-commit install`.
