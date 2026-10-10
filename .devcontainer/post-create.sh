#!/usr/bin/env bash
# Runs once after the devcontainer is created. Installs all project deps.
set -euo pipefail

echo "==> Backend (Poetry)"
cd backend
poetry config virtualenvs.in-project true
poetry install --with=dev,test,debug
# The database and Redis defaults already point at the compose services.
[ -f .env ] || echo "DJANGO_SETTINGS_MODULE = core.settings.debug" > .env
poetry run python manage.py migrate
poetry run python manage.py seed_dev_data --no-input
cd ..

echo "==> Frontend (pnpm)"
cd frontend
[ -f .env ] || cp .env.sample .env
pnpm install --frozen-lockfile
cd ..

echo "==> pre-commit"
pipx install pre-commit >/dev/null 2>&1 || pip install --user pre-commit
# Drop any stale root-owned hook so reinstall isn't blocked.
rm -f .git/hooks/pre-commit 2>/dev/null || true
pre-commit install || echo "    WARN: hook not installed; run 'pre-commit install' on the host."

echo "==> Done. Log in as the test admin: cd backend && poetry run python manage.py dev_session admin.aladar"