#!/bin/sh

APP_PATH="/app"
BACKEND_PATH="$APP_PATH/backend"
${DJANGO_CONTAINER:=true}  # If not defined in environment variable set as true. If true Django commands will run.

##########################
# Postgres check
##########################
echo "Waiting for PostgreSQL on ${DATABASE_HOST:=postgres}:${DATABASE_PORT:=5432}..."
while ! nc -z $DATABASE_HOST $DATABASE_PORT; do
  sleep 0.1
done
echo "PostgreSQL started."

##########################
# Redis check
##########################
REDIS_HOST=$(echo ${CELERY_BROKER:=redis://redis:6379} | awk -F[/:] '{print $4}')
REDIS_PORT=$(echo ${CELERY_BROKER:=redis://redis:6379} | awk -F[/:] '{print $5}')

echo "Waiting for Redis on $REDIS_HOST:$REDIS_PORT..."
while ! nc -z $REDIS_HOST $REDIS_PORT; do
  sleep 0.1
done
echo "Redis started."

##########################
# Django commands
##########################
if [ "$DJANGO_CONTAINER" = true ]; then
  python $BACKEND_PATH/manage.py migrate
fi

exec "$@"
