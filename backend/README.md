# Backend

Django REST API, business logic, Django admin panel and Celery workers for the Request Manager.

**Stack:** Python · Django · Django REST Framework · Celery (Redis) · PostgreSQL · drf-spectacular · social-auth · Sentry

## Setup

Requires Python (version pinned in [`.python-version`](.python-version)), [Poetry](https://python-poetry.org/) and a running PostgreSQL + Redis (start them from the repository root with `docker compose -f docker-compose.dev.yaml up -d`).

```bash
cd backend
poetry install                 # install dependencies into .venv
cp .env.sample .env            # then edit it (see below)
poetry run python manage.py migrate
poetry run python manage.py runserver
```

The API is now available at <http://localhost:8000>.

### Environment

All settings are read from `backend/.env`. Start from [`.env.sample`](.env.sample), which documents every variable and its default. For local development set:

```ini
DJANGO_SETTINGS_MODULE = core.settings.debug
```

### Settings modules

`DJANGO_SETTINGS_MODULE` selects the configuration (`core.settings.*`):

| Module        | Use                                                       |
| ------------- | --------------------------------------------------------- |
| `debug`       | Local development (Django Debug Toolbar, console e-mail). |
| `production`  | Production default.                                       |
| `staging`     | Staging environment.                                      |
| `ci` / `test` | Automated tests and CI.                                   |

## Running the workers

Celery is used for asynchronous tasks and scheduled jobs:

```bash
poetry run celery -A core worker    # task worker
poetry run celery -A core beat      # scheduler
```

## Testing

Tests run with [pytest](https://docs.pytest.org/):

```bash
poetry run pytest
```

Coverage must stay at or above 90% (`fail_under = 90`).

> **PyCharm:** to use pytest instead of the Django test runner, enable _Settings → Python → Django → Do not use Django test runner_, and set the default test runner to pytest under _Settings → Python → Tools → Integrated Tools_.

## Code style

Formatting and linting are enforced by pre-commit (Black, isort, flake8, bandit, pyupgrade, django-upgrade). Install the hooks once from the repository root with `pre-commit install`.

## Upgrading runtime versions

Renovate keeps most versions current automatically. A few values encode the **minimum** supported version and are intentionally left for you to bump by hand when you raise it — Renovate does not touch these floors:

| When you upgrade… | Also bump…                                                                                                                                    |
| ----------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| Python            | `requires-python` in `pyproject.toml`, and the pyupgrade `--py<version>-plus` arg in [`.pre-commit-config.yaml`](../.pre-commit-config.yaml). |
| Django            | the django-upgrade `--target-version` arg in [`.pre-commit-config.yaml`](../.pre-commit-config.yaml).                                         |

The runtime versions themselves live in [`.python-version`](.python-version) (Python) and the `.nvmrc` files (Node) and are bumped by Renovate.

## OpenAPI schema

The REST API is documented with an OpenAPI schema (`backend/schema.yaml`), which is also the source for the frontend's generated API client. Regenerate it after changing serializers, views or endpoints:

```bash
poetry run python manage.py spectacular \
  --file schema.yaml --validate --fail-on-warn \
  --settings core.settings.ci
```

CI fails if the committed schema differs from the generated one.

## Management commands

Run `poetry run python manage.py help` to list every available command. In addition to Django's built-ins, the project ships these commands:

| Command                     | App              | Purpose                                                  |
| --------------------------- | ---------------- | -------------------------------------------------------- |
| `sync_bss_users`            | `common`         | Synchronise users and groups from BSS Login (Authentik). |
| `google_calendar`           | `common`         | Synchronise requests with Google Calendar.               |
| `update_request_status`     | `video_requests` | Recalculate the status of video requests.                |
| `email_daily_reminders`     | `video_requests` | Send daily reminder e-mails.                             |
| `email_overdue_requests`    | `video_requests` | Send the weekly overdue request digests.                 |
| `email_unfinished_requests` | `video_requests` | Notify about unfinished requests.                        |
| `email_weekly_tasks`        | `video_requests` | Send the weekly task summary e-mail.                     |

The e-mail and status commands are normally invoked on a schedule by Celery beat; run them manually for testing or one-off operations.

## Runbooks

### Merging duplicate users

When a person ends up with two accounts, reassign their related objects to the account you want to keep, then delete the duplicate.

The Django admin **delete** page lists every related object for a user; if there are only a few, edit them by hand. For bulk reassignment use the shell — example moving the `Video` objects edited by user `123` to user `234`:

```bash
poetry run python manage.py shell
```

```python
from django.contrib.auth.models import User
from video_requests.models import Video

old = User.objects.get(pk=123)
new = User.objects.get(pk=234)

videos = Video.objects.filter(editor=old)
print(videos)              # review before changing
videos.update(editor=new)
```

Repeat for every relation that points at the old user, then delete it from the admin panel.
