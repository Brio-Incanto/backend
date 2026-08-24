#!/usr/bin/env sh
# Container entrypoint: applies pending migrations, then execs the CMD (uvicorn).
# Set RUN_MIGRATIONS=false to skip (e.g. when migrations are run as a separate step).

set -eu

if [ "${RUN_MIGRATIONS:-true}" = "true" ]; then
    echo "entrypoint: applying system migrations (alembic upgrade head)"
    alembic upgrade head

    if [ "${DRAFT_HISTORY_BACKEND:-memory}" = "tiered" ]; then
        echo "entrypoint: applying draft-archive migrations (alembic -c alembic-draft.ini upgrade head)"
        alembic -c alembic-draft.ini upgrade head
    fi
fi

exec "$@"
