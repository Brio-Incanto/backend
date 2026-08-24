import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from piano_app.adapters.outbound.postgres.draft import draft_metadata
from piano_app.bootstrap.settings import load_environment, load_settings

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

load_environment()
draft_database_url: str | None = load_settings().DRAFT_DATABASE_URL
if draft_database_url is None:
    raise RuntimeError("DRAFT_DATABASE_URL is required to run draft migrations.")

config.set_main_option("sqlalchemy.url", draft_database_url)


def run_migrations_offline() -> None:
    url: str | None = config.get_main_option("sqlalchemy.url")
    if url is None:
        raise RuntimeError("Draft migration database URL is not configured.")

    context.configure(
        url=url,
        target_metadata=draft_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=draft_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_async_migrations())
