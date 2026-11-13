# CLAUDE.md

Request Manager handles the filming and live streaming requests of Budavári Schönherz Stúdió, a university video studio. The user base is small, requesters and the studio's crew, so keep everything simple: understandable code beats clever code, and a small performance gain is not worth a lot of extra code.

Setup and commands live in the READMEs: [root](README.md), [backend](backend/README.md), [frontend](frontend/README.md).

## Before calling something done

Run what the change touches:

```bash
# in frontend/
pnpm lint
pnpm test run
pnpm build
pnpm e2e

# in backend/
uv run pytest

# from the repository root
pre-commit run --files <changed files>
```

In a fresh worktree, copy the gitignored `backend/.env` from the main clone first. Parallel `uv run pytest` runs share Postgres and Redis: give each worktree its own `DATABASE_NAME=rm_<name>` and `CACHE_REDIS=redis://localhost:6379/<n>` as environment variables, which take precedence over `.env`.

For a browser check, don't start a second Vite dev server from `frontend/` in the same checkout: it shares `node_modules/.vite` with the maintainer's and breaks it. Check through `e2e_server` instead (see [Checking a page in a browser](frontend/README.md#checking-a-page-in-a-browser)).

## Commits and branches

Commit messages and PR titles are plain imperative sentences, with no `feat:`-style prefixes. PRs are squash-merged: the PR title becomes the commit on `main`, with an empty body. Renames and deletions go in their own commit, apart from behavior changes, so the diff stays readable.

## Rules

### Frontend

- One Vite app serves two apps: `src/admin/` (PrimeReact, `/admin/*`) and `src/site/` (Tailwind and shadcn/ui, everything else, dark theme only). `src/main.tsx` loads one of them per page, so links between them reload the page.
- Code both apps use lives at the top of `src/`: `api/`, `helpers/`, `hooks/`. Code only one app uses lives in that app's folder. Share logic and wording between the apps, not components.
- `src/api/` is generated from the backend's OpenAPI schema with `pnpm generate-client`; do not edit the generated files. The hand-written ones there are `http.ts`, `errors.ts` and `queryClient.ts`.
- Both apps log in with the session cookie and send the CSRF token. The public build-time values (OAuth client IDs, Sentry DSN, Turnstile site key) are in `frontend/.env.production`.
- Frontend dependencies are pinned to exact versions: add them with `pnpm add --save-exact`. The `@pnpm/exe` entries in `frontend/pnpm-lock.yaml` belong there: pnpm records its own version under `packageManagerDependencies`.
- On admin details pages, a `DetailsRow`'s content is plain text, never a link: navigation goes through the row's `button`, a `LinkButton` labelled "Ugrás" as in `VideoDetailsPage`. In admin editor forms every row uses the full width: split it evenly (`md:col-6`, `md:col-4`) instead of leaving one field half-wide.
- Admin edit forms send only the changed fields (`pickDirtyFields`).

### Backend

- Production has no `ModelBackend`, so only superusers get Django admin permissions; this is intended. The admin may allow more than the API, but neither may let a user create invalid or inconsistent data.

### Data and privacy

- The development database is test data, but its users are real people synced from single sign-on. Never put their data into anything shared: PRs, docs, screenshots, issues.
- Do not send personal data to third-party services. For example, avatars are drawn locally instead of by an avatar service.

### UI copy

- UI copy is Hungarian, and the site uses the informal "te". Prefer "néhány pillanat" to "néhány perc": nothing should feel like it takes minutes.
- Comments on a request are the message thread between the requester and the studio. Word them as messaging the studio ("Üzenetet írhatsz nekünk a felkérésedhez"); never call them "hozzászólás" towards requesters, and do not mention tickets or e-mail. E-mails that only the crew gets may say "hozzászólás".
- Where a form offers "Mentés" and "Mégsem", nothing is saved before "Mentés". Never save instantly next to a cancel button.
