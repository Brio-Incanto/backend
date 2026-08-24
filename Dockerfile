# syntax=docker/dockerfile:1

# --- builder: resolve deps + build the wheel into an isolated venv -----------------
FROM python:3.14-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /build

# Copied separately so dependency resolution is cached across src/ edits.
COPY pyproject.toml README.md ./
COPY src ./src

RUN pip install --upgrade pip && pip install .

# --- runtime: slim image, no compilers/build deps ----------------------------------
FROM python:3.14-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

RUN groupadd --system app && useradd --system --gid app --home-dir /app app

COPY --from=builder /opt/venv /opt/venv

WORKDIR /app

# Migration tooling — not part of the installed package, needed at container start.
COPY alembic.ini alembic-draft.ini ./
COPY alembic ./alembic
COPY alembic_draft ./alembic_draft
COPY entrypoint.sh ./entrypoint.sh
RUN chmod +x ./entrypoint.sh && chown -R app:app /app

USER app

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=5 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/openapi.json', timeout=2)" || exit 1

ENTRYPOINT ["./entrypoint.sh"]
# Runs uvicorn directly (bypassing `python -m piano_app`, which hardcodes
# 127.0.0.1 — fine for local dev, unreachable from outside a container).
# build_app() takes no required args, so it works as a uvicorn factory target.
CMD ["uvicorn", "piano_app.bootstrap.container:build_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
