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

Builds also read two Sentry variables, which the Docker workflow sets: `SENTRY_RELEASE` is the release the app reports, and with `SENTRY_AUTH_TOKEN` the build uploads its source maps to Sentry and removes them from `build/`. Without the token the source maps stay for `pnpm analyze`.

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

| Script                 | Description                                          |
| ---------------------- | ---------------------------------------------------- |
| `pnpm start`           | Start the Vite dev server (HTTPS, port 5173).        |
| `pnpm start:network`   | Same, exposed on the local network (`--host`).       |
| `pnpm build`           | Type-check (`tsc --noEmit`) and build into `build/`. |
| `pnpm preview`         | Serve the production build locally.                  |
| `pnpm lint`            | Run ESLint.                                          |
| `pnpm lint:fix`        | Run ESLint with autofix.                             |
| `pnpm format`          | Format sources with Prettier.                        |
| `pnpm generate-client` | Regenerate the API client from the backend schema.   |
| `pnpm analyze`         | Inspect the bundle with source-map-explorer.         |

## Code style

Formatting and linting (Prettier + ESLint) are enforced by pre-commit. Install the hooks once from the repository root with `pre-commit install`.
