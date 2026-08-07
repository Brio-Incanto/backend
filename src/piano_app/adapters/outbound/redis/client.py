from redis.asyncio import Redis


def create_client(*, database_url: str) -> Redis:
    """The async Redis client. Construction only — no connection is opened until
    it's first used, so this is safe to call at app build time (mirrors
    ``postgres.engine.create_engine``)."""
    return Redis.from_url(database_url, decode_responses=True)
