.PHONY: infra migrate run up smoke down lint typecheck test check docker-build docker-up

# System Postgres + draft Postgres + Redis only (NOT the app container — `run`
# below starts the API locally via .venv), waits for all to report healthy.
infra:
	docker compose up -d postgres draft-postgres redis
	@echo "waiting for system postgres + draft postgres + redis..."
	@until [ "$$(docker inspect -f '{{.State.Health.Status}}' pianoappbackend-postgres-1 2>/dev/null)" = "healthy" ] && \
	      [ "$$(docker inspect -f '{{.State.Health.Status}}' pianoappbackend-draft-postgres-1 2>/dev/null)" = "healthy" ] && \
	      [ "$$(docker inspect -f '{{.State.Health.Status}}' pianoappbackend-redis-1 2>/dev/null)" = "healthy" ]; do \
	    sleep 1; \
	done
	@echo "infra up"

# Applies all pending Alembic migrations (idempotent — safe to re-run).
migrate:
	.venv/bin/alembic upgrade head
	.venv/bin/alembic -c alembic-draft.ini upgrade head

# Starts the API on http://127.0.0.1:8000 (python -m piano_app).
run:
	.venv/bin/python -m piano_app

# One command: infra -> migrate -> run. Ctrl-C stops the API; containers keep running
# (see `make down` to also tear those down).
up: infra migrate run

# Full-app smoke: needs infra+migrate already applied (run `make infra migrate` first,
# or `make up` in another terminal). Exercises drafts/edit/save end-to-end.
smoke:
	DRAFT_HISTORY_BACKEND=redis .venv/bin/python scripts/smoke.py

down:
	docker compose down

# ruff check + format check (no fixes applied).
lint:
	.venv/bin/ruff check .
	.venv/bin/ruff format --check .

# mypy --strict-ish over src (see pyproject [tool.mypy]).
typecheck:
	.venv/bin/mypy src

# Runs the test suite (see README for currently-known failures).
test:
	.venv/bin/pytest

# lint + typecheck + test, same checks CI runs.
check: lint typecheck test

# Builds the app image (Dockerfile) without starting anything.
docker-build:
	docker compose build app

# Full stack in containers: infra + app, migrations applied by entrypoint.sh.
# `make down` tears the whole stack (infra + app) back down.
docker-up:
	docker compose up --build
