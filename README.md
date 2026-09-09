# Piano App — Backend

FastAPI backend for the piano notation editor. It holds the score model and
the mutation engine that edits it, behind a thin HTTP layer, with Google
Sign-In auth and a two-tier draft store (Redis hot, Postgres cold) for
in-progress edits.

## Requirements

- Python 3.14
- Docker and Docker Compose, either for the full stack or just for
  Postgres and Redis while the app runs on the host

## Configuration

Everything is configured through environment variables, read by
[`src/piano_app/bootstrap/settings/models.py`](src/piano_app/bootstrap/settings/models.py).

```bash
cp .env.example .env
```

`DATABASE_URL` and `JWT_SECRET` are required and the app will not start
without them. The rest have defaults; [`.env.example`](.env.example)
documents what each one does. The ones worth knowing about:

- `DRAFT_HISTORY_BACKEND` picks the draft adapter. `memory` (the default)
  runs in a single process with no external services. `redis` uses the hot
  tier only. `tiered` uses Redis for hot state plus a separate Postgres for
  the cold archive, which is what the Compose stack below runs.
- `DATABASE_URL` holds canon scores and auth data. It is always needed,
  whichever draft backend you pick.
- `DRAFT_DATABASE_URL` and `REDIS_URL` are only read by `redis` and
  `tiered`.
- `JWT_SECRET` must be at least 64 bytes.

## Running locally

```bash
python -m venv .venv
```

```bash
.venv/bin/pip install -e ".[dev]"
```

Start Postgres (two instances) and Redis in containers, apply migrations,
then serve the API on `http://127.0.0.1:8000`:

```bash
make infra
```

```bash
make migrate
```

```bash
make run
```

`make up` does all three at once. Ctrl-C stops the API and leaves the
containers running; `make down` stops those too.

## Running the full stack in Docker

`make docker-up` builds the app image and starts it next to Postgres and
Redis on the Compose network. `entrypoint.sh` applies migrations before the
server comes up. The API listens on `http://localhost:8000`, and `make down`
stops everything.

The `app` service always runs with `DRAFT_HISTORY_BACKEND=tiered` and with
`DATABASE_URL`, `DRAFT_DATABASE_URL` and `REDIS_URL` pointed at the
`postgres`, `draft-postgres` and `redis` containers. Those override whatever
`.env` holds for host-side development, since `localhost` means something
else inside a container. Auth and CORS settings still come from `.env`
through `env_file`.

To build the image without starting anything, run `make docker-build`.

### Migrations in the container

`entrypoint.sh` runs `alembic upgrade head` on every start, plus
`alembic -c alembic-draft.ini upgrade head` when `DRAFT_HISTORY_BACKEND` is
`tiered`. Set `RUN_MIGRATIONS=false` to skip that and apply migrations
yourself.

## Migrations by hand

There are two Alembic setups, one for system data and one for the draft
cold archive, each with its own config and history:

```bash
.venv/bin/alembic upgrade head
```

```bash
.venv/bin/alembic -c alembic-draft.ini upgrade head
```

`make migrate` runs both.

## Tests, linting, type checks

```bash
make lint
```

```bash
make typecheck
```

```bash
make test
```

`make check` runs all three, the same set CI runs on every push and pull
request.

Known failures: 15 tests under `tests/unit/adapters/outbound/` are red
because they still call the older `VersionedDraftDocument` and
`InMemoryDraftHistory` constructors. Everything else passes.

There is also an end-to-end smoke test against a running instance. Bring up
infra and apply migrations first, then:

```bash
make smoke
```

## CI

[`.github/workflows/ci.yml`](.github/workflows/ci.yml) runs on every push to
`main` and on every pull request: `ruff check`, `ruff format --check`,
`mypy`, `pytest`, and a Docker build that validates the image without
pushing it.

## Layout

```
src/piano_app/
  domain/       score document model and mutation engine
  application/  use cases and ports
  adapters/     inbound HTTP, outbound Postgres/Redis/codecs
  bootstrap/    settings and DI container (FastAPI assembly)
alembic/            migrations for system data (canon scores + auth)
alembic_draft/      migrations for the draft cold archive
docs/               design notes
scripts/smoke.py    end-to-end smoke test against a running instance
```
