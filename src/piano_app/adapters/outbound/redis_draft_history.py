import json
from typing import Literal

from redis.asyncio import Redis
from redis.commands.core import AsyncScript

from piano_app.adapters.outbound.codec import ScoreDocumentCodec
from piano_app.application.ports.draft_store import DraftNotFoundError
from piano_app.domain.score.models import ScoreDocument

# max number of revisions per draft
MAX_DRAFT_HISTORY_SIZE: int = 30
# revision history is automatically deleted from Redis cache after 5 minutes without any edit
# (load() is read-only and does not refresh the TTL)
DRAFT_TTL_SECONDS: int = 300

# Lua scripts are used to achieve atomicity of operations on Redis
_LOAD_SCRIPT: str = """
local revisions_key = KEYS[1]
local cursor_key = KEYS[2]

if redis.call('EXISTS', revisions_key) == 0
 or redis.call('EXISTS', cursor_key) == 0
then
    return false
end

local cursor = tonumber(redis.call('GET', cursor_key))
return redis.call('LINDEX', revisions_key, cursor)
"""

# when committing a new revision, the remaining redo revisions are removed
# if the number of revisions exceeds the limit, the oldest one is removed
#
# TODO: if the draft vanished between load and commit (TTL/eviction race), this
# currently fails with DraftNotFoundError, losing the caller's edit. The real fix
# is NOT here -- it belongs in the application-service orchestrator, as part of
# the future hot(Redis)/cold(Postgres) get-or-create cascade: on a miss, load from
# cold storage, hydrate it back into the hot cache, and only then apply/commit.
# This adapter should stay a plain hot-tier store and not try to "recover" on its
# own by inventing data the orchestrator doesn't know about.
_COMMIT_SCRIPT: str = """
local revisions_key = KEYS[1]
local cursor_key = KEYS[2]

if redis.call('EXISTS', revisions_key) == 0
 or redis.call('EXISTS', cursor_key) == 0
then
    return -1
end

local new_revision = ARGV[1]
local max_size = tonumber(ARGV[2])

local cursor = tonumber(redis.call('GET', cursor_key))
redis.call('LTRIM', revisions_key, 0, cursor)
redis.call('RPUSH', revisions_key, new_revision)

if redis.call('LLEN', revisions_key) > max_size then
    redis.call('LTRIM', revisions_key, -max_size, -1)
end

local new_cursor = redis.call('LLEN', revisions_key) - 1
redis.call('SET', cursor_key, new_cursor)
return new_cursor
"""

_UNDO_SCRIPT: str = """
local cursor_key = KEYS[1]
if redis.call('EXISTS', cursor_key) == 0 then
    return -1
end

local cursor = tonumber(redis.call('GET', cursor_key))

if cursor <= 0 then
    return 0
end

redis.call('DECR', cursor_key)
return 1
"""

_REDO_SCRIPT: str = """
local cursor_key = KEYS[1]
local revisions_key = KEYS[2]

if redis.call('EXISTS', cursor_key) == 0
 or redis.call('EXISTS', revisions_key) == 0
then
    return -1
end

local cursor = tonumber(redis.call('GET', cursor_key))
local length = redis.call('LLEN', revisions_key)

if cursor >= length - 1 then
    return 0
end

redis.call('INCR', cursor_key)
return 1
"""

type RedisResponseCode = Literal[-1, 0, 1]


class RedisDraftHistory:
    """Redis-backed draft history.

    For each draft there are two keys: one for the revisions (``draft:{id}:revisions``),
    and one for the cursor (``draft:{id}:cursor``), pointing at the current revision.
    A record of one draft is splitted in two keys to avoid overwriting of heavy revisions,
    atomicity is achieved by a Lua scripts.
    """

    def __init__(self, *, client: Redis, codec: ScoreDocumentCodec) -> None:
        self._client: Redis = client
        self._codec: ScoreDocumentCodec = codec

        self._load_script: AsyncScript = client.register_script(_LOAD_SCRIPT)
        self._commit_script: AsyncScript = client.register_script(_COMMIT_SCRIPT)
        self._undo_script: AsyncScript = client.register_script(_UNDO_SCRIPT)
        self._redo_script: AsyncScript = client.register_script(_REDO_SCRIPT)

    # temporary function for testing purposes
    async def ensure_seeded(self, *, draft_id: str, document: ScoreDocument) -> None:
        """Writes ``document`` as the draft's first revision,
        unless the draft already exists.
        """
        cursor_key: str = self._cursor_key(draft_id=draft_id)
        revisions_key: str = self._revisions_key(draft_id=draft_id)

        if await self._client.exists(cursor_key, revisions_key) == 2:
            await self._refresh_ttl(draft_id=draft_id)
            return

        async with self._client.pipeline() as pipe:
            # delete first: if only ONE of the two keys survived (partial eviction),
            # a plain rpush would append onto stale leftover revisions instead of starting
            # clean, silently corrupting the draft (cursor pointing at old garbage).

            # delete, rpush and set only add commands to the command_stack, so no IO operation yet
            # no need to await them
            pipe.delete(revisions_key, cursor_key)
            pipe.rpush(revisions_key, self._serialize(document))
            pipe.set(cursor_key, 0)
            await pipe.execute()

        await self._refresh_ttl(draft_id=draft_id)

    async def load(self, *, draft_id: str) -> ScoreDocument:
        raw: bytes | str | None = await self._load_script(
            keys=[self._revisions_key(draft_id=draft_id), self._cursor_key(draft_id=draft_id)]
        )
        if raw is None:
            raise DraftNotFoundError(draft_id=draft_id)

        return self._deserialize(self._to_str(raw))

    async def commit(self, *, draft_id: str, document: ScoreDocument) -> None:
        commited_code: RedisResponseCode = await self._commit_script(
            keys=[self._revisions_key(draft_id=draft_id), self._cursor_key(draft_id=draft_id)],
            args=[self._serialize(document), MAX_DRAFT_HISTORY_SIZE],
        )

        if commited_code == -1:
            raise DraftNotFoundError(draft_id=draft_id)

        await self._refresh_ttl(draft_id=draft_id)

    async def undo(self, *, draft_id: str) -> bool:
        undone_code: RedisResponseCode = await self._undo_script(
            keys=[self._cursor_key(draft_id=draft_id)]
        )

        if undone_code == -1:
            raise DraftNotFoundError(draft_id=draft_id)

        await self._refresh_ttl(draft_id=draft_id)
        return undone_code == 1

    async def aclose(self) -> None:
        """Closes the underlying Redis connection pool. Call on app shutdown."""
        await self._client.aclose()

    async def redo(self, *, draft_id: str) -> bool:
        redone_code: RedisResponseCode = await self._redo_script(
            keys=[self._cursor_key(draft_id=draft_id), self._revisions_key(draft_id=draft_id)]
        )

        if redone_code == -1:
            raise DraftNotFoundError(draft_id=draft_id)

        await self._refresh_ttl(draft_id=draft_id)
        return redone_code == 1

    # Redis is already created with decode_responses=True, this is needed for static typying only
    @staticmethod
    def _to_str(value: bytes | str) -> str:
        return value.decode() if isinstance(value, bytes) else value

    # TODO consider making a decorator for this functionality
    async def _refresh_ttl(self, *, draft_id: str) -> None:
        async with self._client.pipeline() as pipe:
            pipe.expire(self._revisions_key(draft_id=draft_id), DRAFT_TTL_SECONDS)
            pipe.expire(self._cursor_key(draft_id=draft_id), DRAFT_TTL_SECONDS)
            await pipe.execute()

    def _serialize(self, document: ScoreDocument) -> str:
        return json.dumps(self._codec.serialize(document))

    def _deserialize(self, revision: str) -> ScoreDocument:
        return self._codec.deserialize(json.loads(revision))

    @staticmethod
    def _revisions_key(*, draft_id: str) -> str:
        return f"draft:{draft_id}:revisions"

    @staticmethod
    def _cursor_key(*, draft_id: str) -> str:
        return f"draft:{draft_id}:cursor"
