# Piano App — Backend

FastAPI backend for the piano notation editor: a hexagonal/DDD score-editing
engine (streaming mutation pipeline over a document model) behind a thin HTTP
layer, with Google Sign-In auth and a two-tier (Redis hot / Postgres cold)
draft store for in-progress edits.

Design principles and the current state of the refactor are tracked in
[`CLAUDE.md`](CLAUDE.md) / [`AGENTS.md`](AGENTS.md) (auto-loaded by AI
assistants working in this repo) and [`docs/CONTEXT.md`](docs/CONTEXT.md).
This README covers running and deploying the service, not its internal
design.

## Requirements

- Python 3.14
- Docker + Docker Compose (either for full-stack local dev, or just to run
  Postgres/Redis while the app runs on the host)

## Configuration

All configuration is environment variables — nothing has a default baked
into source (see [`src/piano_app/bootstrap/settings/models.py`](src/piano_app/bootstrap/settings/models.py));
the app refuses to start if a required one is missing.

```bash
cp .env.example .env
```

Then fill in every value in `.env`. See the comments in
[`.env.example`](.env.example) for what each one does. Notably:

- `DRAFT_HISTORY_BACKEND` — `memory` (default, single process, no external
  services), `redis` (hot tier only), or `tiered` (Redis hot + Postgres
  cold archive — what the Docker Compose stack below runs).
- `DATABASE_URL` — always required (canon scores + auth), independent of the
  draft backend.
- `DRAFT_DATABASE_URL` / `REDIS_URL` — only required for `redis`/`tiered`.
- `JWT_SECRET` — must be at least 64 bytes.

## Running locally (host Python)

```bash
python -m venv .venv
```

```bash
.venv/bin/pip install -e ".[dev]"
```

Bring up just the infra containers (Postgres ×2 + Redis), apply migrations,
and start the API on `http://127.0.0.1:8000`:

```bash
make infra
```

```bash
make migrate
```

```bash
make run
```

Or all three in one go (`make up`; Ctrl-C stops the API, containers keep
running — `make down` tears those down too).

## Running with Docker Compose (full stack)

Builds the app image and starts it alongside Postgres ×2 + Redis, all wired
together on the compose network; `entrypoint.sh` applies migrations
automatically before the server starts.

```bash
make docker-up
```

The API is then reachable at `http://localhost:8000`. `make down` stops
everything.

Note: inside the compose network the `app` service always runs with
`DRAFT_HISTORY_BACKEND=tiered` and internal `DATABASE_URL` /
`DRAFT_DATABASE_URL` / `REDIS_URL` values pointing at the other containers
(`postgres`, `draft-postgres`, `redis`) — these override whatever `.env`
has for host-side dev, since `localhost` isn't reachable from inside a
container. Everything else (JWT/auth/CORS settings) is read from `.env` via
`env_file`.

To only build the image without starting anything: `make docker-build`.

### Migrations inside the container

`entrypoint.sh` runs `alembic upgrade head` on every container start (and
also `alembic -c alembic-draft.ini upgrade head` when
`DRAFT_HISTORY_BACKEND=tiered`). Set `RUN_MIGRATIONS=false` in the
environment to skip this and apply migrations as a separate step instead.

## Migrations (manual)

Two independent Alembic setups — system data and the draft cold-archive —
each with its own config and its own migration history:

```bash
.venv/bin/alembic upgrade head
```

```bash
.venv/bin/alembic -c alembic-draft.ini upgrade head
```

(`make migrate` runs both.)

## Testing, linting, type-checking

```bash
make lint
```

```bash
make typecheck
```

```bash
make test
```

`make check` runs all three — the same checks CI runs on every push/PR.

**Known state:** the domain/geometry/context test suites are green; a
cluster of persistence-adapter tests (`tests/unit/adapters/outbound/`) is
currently red due to a documented API drift between those tests and the
current `VersionedDraftDocument`/`InMemoryDraftHistory` constructors — see
the "TESTS ADDED" / pytest-config-fix note in `CLAUDE.md`. This is tracked,
pre-existing debt, not something CI failing on it should be read as a
regression in your change.

## CI

[`.github/workflows/ci.yml`](.github/workflows/ci.yml) runs on every push to
`main` and every pull request: `ruff check` + `ruff format --check`, `mypy`,
`pytest`, and a Docker build validation (image is built, not pushed).

## Project layout

```
src/piano_app/
  domain/       hexagonal core: score document model + mutation engine (see CLAUDE.md)
  application/  use cases / ports
  adapters/     inbound (HTTP) and outbound (Postgres, Redis, codecs) adapters
  bootstrap/    settings + DI container (FastAPI app assembly)
alembic/            migrations for system data (canon scores + auth)
alembic_draft/      migrations for the draft cold-archive
docs/               design docs (CONTEXT.md, catalog-plan.md, domain-style.md)
scripts/smoke.py    end-to-end smoke test against a running instance
```
