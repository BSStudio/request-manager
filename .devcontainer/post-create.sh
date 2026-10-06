#!/usr/bin/env bash
# Runs once after the devcontainer is created. Installs all project deps.
set -euo pipefail

echo "==> Backend (Poetry)"
cd backend
poetry config virtualenvs.in-project true
poetry install --with=dev,test,debug
cd ..

echo "==> Admin dashboard (pnpm)"
cd frontend-admin && pnpm install --frozen-lockfile && cd ..

echo "==> pre-commit"
pipx install pre-commit >/dev/null 2>&1 || pip install --user pre-commit
# Drop any stale root-owned hook so reinstall isn't blocked.
rm -f .git/hooks/pre-commit 2>/dev/null || true
pre-commit install || echo "    WARN: hook not installed; run 'pre-commit install' on the host."

echo "==> Done. Reminder: create backend/.env (DATABASE_HOST=postgres, CELERY_BROKER=redis://redis:6379)."