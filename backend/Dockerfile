# syntax=docker/dockerfile:1
# Keep this syntax directive! It's used to enable Docker BuildKit
# Based on https://gist.github.com/usr-ein/c42d98abca3cb4632ab0c2c6aff8c88a

###################################
#  FOR DEVELOPMENT PURPOSES ONLY  #
###################################

##################################################

# Stage 1 - Backend base
FROM python:3.14-alpine AS backend-base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0 \
    \
    PYSETUP_PATH="/opt/pysetup" \
    VIRTUAL_ENV="/opt/pysetup/.venv"

# Add Venv to Path
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

##################################################

# Stage 2 - Backend builder

# Use backend-base image as base
FROM backend-base AS backend-builder

# Install build dependencies
RUN apk update && apk add postgresql-dev gcc musl-dev python3-dev

# Install uv
COPY --from=ghcr.io/astral-sh/uv:0.13.0 /uv /bin/uv

# Set work directory
WORKDIR $PYSETUP_PATH

# Copy project requirement files here to ensure they will be cached
COPY uv.lock pyproject.toml ./

# Install runtime dependencies
# The --mount will mount the buildx cache directory to where
# uv stores its cache so that it can re-use it
RUN --mount=type=cache,target=/root/.cache \
    uv sync --locked --no-group dev --no-group test --group prod

##################################################

# Stage 3 - Final image

# Use backend-base image as base
FROM backend-base AS production

# Copy built runtime dependencies from builder container
COPY --from=backend-builder $PYSETUP_PATH $PYSETUP_PATH

# Install runtime dependency for psycopg[c]
RUN apk update && apk add --no-cache libpq

# Copy everything over to Docker environment
COPY . /app/backend

# Collect static files
WORKDIR /app/backend
RUN python manage.py collectstatic --no-input --clear --settings=core.settings.base

# Open port
EXPOSE 8000

# Set health check
HEALTHCHECK --start-period=30s --interval=5m \
    CMD python manage.py health_check readyz --no-http

# Do the migrations and start the server
CMD ["sh", "-c", "python manage.py migrate; gunicorn --bind=0.0.0.0:8000 --workers=5 --threads=2 --timeout=60 --graceful-timeout=30 core.wsgi"]
