from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


def create_engine(*, database_url: str) -> AsyncEngine:
    """The async engine. Construction only — no connection is opened until it's
    first used, so this is safe to call at app build time."""
    return create_async_engine(database_url)


def create_session_factory(*, engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """A session factory the Postgres adapters open a session from per operation.

    ``expire_on_commit=False`` is deliberate and load-bearing under async: with
    the default (True), a mapped object's attributes are expired after commit and
    the next attribute access triggers a lazy refresh — but under async that
    refresh is IO happening inside a plain (sync) attribute access, which raises
    ``MissingGreenlet`` (verified). Adapters read everything they need (including
    ``to_domain``) while the session is open and never want a post-commit expiry.
    """
    return async_sessionmaker(engine, expire_on_commit=False)
