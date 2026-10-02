<p align="center">
  <img src="https://bsstudio.hu/system/files/site_content/logo/bss_logo_169.png" width="50%" alt="Budavári Schönherz Stúdió logo">
</p>

---

# Request Manager

Workflow Support System for managing video shooting, filming and live-streaming
requests of [Budavári Schönherz Stúdió](https://bsstudio.hu).

[![Backend CI](https://github.com/BSStudio/request-manager/actions/workflows/backend.yml/badge.svg)](https://github.com/BSStudio/request-manager/actions/workflows/backend.yml)
[![Frontend CI](https://github.com/BSStudio/request-manager/actions/workflows/frontend.yml/badge.svg)](https://github.com/BSStudio/request-manager/actions/workflows/frontend.yml)
[![Frontend CI - Admin Dashboard](https://github.com/BSStudio/request-manager/actions/workflows/frontend-admin.yml/badge.svg)](https://github.com/BSStudio/request-manager/actions/workflows/frontend-admin.yml)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)

## Overview

The project is a monorepo made up of two deployable applications backed by PostgreSQL and Redis:

| Component                          | Stack                                                                  | Description                                                                               |
| ---------------------------------- | ---------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| [`backend`](backend)               | Django, Django REST Framework, Celery, PostgreSQL                      | REST API, business logic, admin panel and async workers.                                  |
| [`frontend-admin`](frontend-admin) | React, TypeScript, Tailwind CSS, shadcn/ui, PrimeReact, TanStack Query | Public site where users submit and follow up requests, and the admin dashboard for staff. |

[`frontend`](frontend), the previous public site, is no longer built or deployed and will be removed.

The frontend is a static build served by the backend in production (through WhiteNoise). Authentication is handled via OAuth2 (AuthSCH, BSS Login, Google, Microsoft) with JWT tokens.

```mermaid
flowchart TD
    frontend["frontend-admin<br/>(public site + admin)"] -->|REST · JWT| backend
    backend["backend<br/>(Django + Celery)"] --> postgres[("PostgreSQL")]
    backend --> redis[("Redis")]
```

## Repository layout

```
.
├── backend/         Django REST API, Celery workers, admin panel
├── frontend/        Previous public site, no longer used
├── frontend-admin/  Public site and admin dashboard (Vite, TypeScript)
├── .devcontainer/   VS Code dev container (Python + Node + Poetry)
├── docker-compose.dev.yaml   PostgreSQL + Redis for local development
└── docker-compose.yaml       Full production-like stack
```

## Getting started

The fastest way to get a complete toolchain is the **dev container**, which
provisions Python, Node and Poetry and starts PostgreSQL + Redis automatically.

### Option A — Dev Container (recommended)

1. Install [Docker Desktop](https://www.docker.com/products/docker-desktop/) and
   the [VS Code Dev Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)
   extension.
2. Open the repository in VS Code and run **Dev Containers: Reopen in Container**.
3. Once the post-create step finishes, create the `.env` files (see each
   component's README) and run the apps.

> **Windows + WSL:** if the container fails to start with a
> `distro-services/<distro>.sock: no such file` error, enable Docker Desktop →
> Settings → Resources → **WSL Integration** for your distro (e.g. `Debian`).

### Option B — Manual setup

Start the infrastructure, then follow each component's README:

```bash
docker compose -f docker-compose.dev.yaml up -d   # PostgreSQL + Redis
```

- [Backend setup](backend/README.md)
- [Frontend setup](frontend-admin/README.md)

**Prerequisites for manual setup:** Python + [Poetry](https://python-poetry.org/)
and Node.js — the exact versions are pinned in `backend/.python-version` and the
`.nvmrc` files — plus Docker for PostgreSQL + Redis.

## Development

This repository uses [pre-commit](https://pre-commit.com/) for formatting and
linting (Black, isort, flake8, Prettier, ESLint and more). Install the hooks at
once from the repository root:

```bash
pipx install pre-commit   # or: pip install pre-commit
pre-commit install
```

Run all checks manually with `pre-commit run --all-files`.

Node and Python versions are pinned in a single place each and kept up to date
by Renovate:

- Node.js — `frontend/.nvmrc` and `frontend-admin/.nvmrc`
- Python — `backend/.python-version`

## License

Distributed under the GNU General Public License v3.0. See [`LICENSE`](LICENSE).
