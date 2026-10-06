# CLAUDE.md

Request Manager handles the filming and live streaming requests of Budavári Schönherz Stúdió, a university video studio. The user base is small, requesters and the studio's crew, so keep everything simple: understandable code beats clever code, and a small performance gain is not worth a lot of extra code.

Setup and commands live in the READMEs: [root](README.md), [backend](backend/README.md), [frontend](frontend/README.md).

## How we work

- Work in small steps. After each step, stop and report what changed and how you checked it, then suggest a one-line commit message: a plain sentence, no `feat:`-style prefixes.
- The maintainer reviews and commits every step. Never commit, push or stage files yourself.
- Keep each PR to one kind of change. Renames and deletions go in their own PR, apart from behavior changes, so the diff stays readable. PR titles are short plain sentences; the description is written for reviewers.
- For review comments (people or bots), check each one against the current code, fix the ones that still hold and say briefly why you skipped the rest.
- Before handing work over, run what applies: `pnpm lint` and `pnpm build` in `frontend/`, `poetry run pytest` in `backend/`, and `pre-commit run --files <changed files>`. Check UI changes in a browser.
- Start your own dev servers on free ports. Never stop or reuse the ones the maintainer is running.
- Ask before changing anything global on the machine: installed tools, PATH, global config.

## Code

- Match the surrounding code: naming, structure, idioms.
- Comment only what the code cannot say: a hidden reason, a constraint, a gotcha. Do not restate names, explain a refactor, or describe what a component is. Never repeat the same comment in several files.
- Frontend dependencies are pinned to exact versions. Do not commit lockfile churn from a standalone pnpm build (`@pnpm/exe` entries).

## Frontend layout

- One Vite app serves two apps: `src/admin/` (PrimeReact, `/admin/*`) and `src/site/` (Tailwind and shadcn/ui, everything else, dark theme only). `src/main.tsx` loads one of them per page, so links between them reload the page.
- Code both apps use lives at the top of `src/`: `api/`, `helpers/`, `hooks/`. Code only one app uses lives in that app's folder. Share logic and wording between the apps, not components.
- `src/api/` is generated from the backend's OpenAPI schema with `pnpm generate-client`; do not edit the generated files. The hand-written ones there are `http.ts`, `errors.ts` and `queryClient.ts`.
- Both apps log in with the session cookie and send the CSRF token. The public build-time values (OAuth client IDs, Sentry DSN, Turnstile site key) are in `frontend/.env.production`.

## Data and privacy

- The development database is test data, but its users are real people synced from single sign-on. Never put their data into anything shared: PRs, docs, screenshots, issues.
- Do not send personal data to third-party services. For example, avatars are drawn locally instead of by an avatar service.

## Writing

- UI copy is Hungarian and must sound natural, not translated. The site uses the informal "te". Prefer "néhány pillanat" to "néhány perc": nothing should feel like it takes minutes.
- Comments on a request are the message thread between the requester and the studio. Word them as messaging the studio ("Üzenetet írhatsz nekünk a felkérésedhez"); never call them "hozzászólás" towards requesters, and do not mention tickets or e-mail. E-mails that only the crew gets may say "hozzászólás".
- Where a form offers "Mentés" and "Mégsem", nothing is saved before "Mentés". Never save instantly next to a cancel button.
- Code, commits, PRs and docs are in English.
- In Markdown, write each paragraph on one line; do not hard-wrap prose.
