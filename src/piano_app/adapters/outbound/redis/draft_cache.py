import json
from typing import Final

from redis.asyncio import Redis
from redis.commands.core import AsyncScript

from piano_app.adapters.outbound.shared.codec import ScoreDocumentCodec
from piano_app.adapters.outbound.shared.draft_snapshot import DraftSnapshot
from piano_app.application.ports.score.draft_store import (
    DraftNotFoundError,
    DraftVersionClashError,
    VersionedDraftDocument,
)
from piano_app.domain.score.document import ScoreDocument

from .shared_lua_scripts import _COMMIT_SCRIPT, _LOAD_SCRIPT, _REDO_SCRIPT, _UNDO_SCRIPT

# TODO compress 4 keys (cursor, version, author, score) into 1 key (draft:draft_id:meta)
#  that is of HSET type
# same sentinel/reasoning as RedisDraftHistory's _NO_SCORE_SENTINEL — duplicated
# rather than shared, matching the existing duplication of _to_str/_serialize/
# _deserialize/key-builders below (no inheritance between the two Redis adapters,
# see RedisDraftCache's own docstring).
_NO_SCORE_SENTINEL: Final[str] = "none"

# own to RedisDraftCache only (RedisDraftHistory has neither hydrate() nor
# load_snapshot()); load/commit/undo/redo are identical hot-tier mechanics shared
# by both, imported from .shared_lua_scripts.
_HYDRATE_SCRIPT: str = """
local revisions_key = KEYS[1]
local cursor_key = KEYS[2]
local version_key = KEYS[3]
local author_key = KEYS[4]
local score_key = KEYS[5]

local cursor = ARGV[1]
local version = ARGV[2]
local author_id = ARGV[3]
local score_id = ARGV[4]
local ttl_seconds = ARGV[5]
local revisions_start_arg = 6

local keys_count = redis.call(
    'EXISTS', revisions_key, cursor_key, version_key, author_key, score_key
)
if keys_count == 5 then
    return {'exists'}
end
if keys_count ~= 0 then
    return {'corrupt', 'partial_keys'}
end

if ARGV[revisions_start_arg] == nil then
    return {'corrupt', 'missing_revisions'}
end

redis.call('RPUSH', revisions_key, unpack(ARGV, revisions_start_arg))
redis.call('SET', cursor_key, cursor)
redis.call('SET', version_key, version)
redis.call('SET', author_key, author_id)
redis.call('SET', score_key, score_id)

redis.call('EXPIRE', revisions_key, ttl_seconds)
redis.call('EXPIRE', cursor_key, ttl_seconds)
redis.call('EXPIRE', version_key, ttl_seconds)
redis.call('EXPIRE', author_key, ttl_seconds)
redis.call('EXPIRE', score_key, ttl_seconds)

return {'ok'}
"""

_LOAD_SNAPSHOT_SCRIPT: str = """
local revisions_key = KEYS[1]
local cursor_key = KEYS[2]
local version_key = KEYS[3]
local author_key = KEYS[4]
local score_key = KEYS[5]

local keys_count = redis.call(
    'EXISTS', revisions_key, cursor_key, version_key, author_key, score_key
)
if keys_count == 0 then
    return {'not_found'}
end
if keys_count ~= 5 then
    return {'corrupt', 'partial_keys'}
end

local cursor = tonumber(redis.call('GET', cursor_key))
local revisions_length = redis.call('LLEN', revisions_key)
if cursor == nil or cursor < 0 or cursor >= revisions_length then
    return {'corrupt', 'cursor_out_of_range'}
end

local version = redis.call('GET', version_key)
if tonumber(version) == nil then
    return {'corrupt', 'invalid_version'}
end

return {
    'ok',
    cursor,
    version,
    redis.call('GET', author_key),
    redis.call('GET', score_key),
    unpack(redis.call('LRANGE', revisions_key, 0, -1))
}
"""


class RedisDraftCache:
    def __init__(
        self,
        *,
        client: Redis,
        codec: ScoreDocumentCodec,
        max_history_size: int = 30,
        ttl_seconds: int = 300,
    ) -> None:
        if max_history_size < 1:
            raise ValueError(f"max_history_size must be >= 1, got {max_history_size!r}.")
        if ttl_seconds < 1:
            raise ValueError(f"ttl_seconds must be >= 1, got {ttl_seconds!r}.")

        self._client: Redis = client
        self._codec: ScoreDocumentCodec = codec

        # max number of revisions per draft
        self._MAX_DRAFT_HISTORY_SIZE: Final[int] = max_history_size
        # revision history is automatically deleted from Redis cache after specified TTL
        # (load() is read-only and does not refresh the TTL)
        self._DRAFT_TTL_SECONDS: Final[int] = ttl_seconds

        self._load_script: AsyncScript = client.register_script(_LOAD_SCRIPT)
        self._commit_script: AsyncScript = client.register_script(_COMMIT_SCRIPT)
        self._undo_script: AsyncScript = client.register_script(_UNDO_SCRIPT)
        self._redo_script: AsyncScript = client.register_script(_REDO_SCRIPT)
        self._hydrate_script: AsyncScript = client.register_script(_HYDRATE_SCRIPT)
        self._load_snapshot_script: AsyncScript = client.register_script(_LOAD_SNAPSHOT_SCRIPT)

    async def load(self, *, draft_id: str) -> VersionedDraftDocument:
        response: list[bytes | str | int] = await self._load_script(
            keys=[
                self._revisions_key(draft_id=draft_id),
                self._cursor_key(draft_id=draft_id),
                self._version_key(draft_id=draft_id),
                self._author_key(draft_id=draft_id),
                self._score_key(draft_id=draft_id),
            ]
        )

        response_code: str = self._to_str(response[0])
        response_body: list[bytes | str | int] = response[1:]

        match response_code:
            case "ok":
                revision: str = self._to_str(response_body[0])
                version: int = int(self._to_str(response_body[1]))
                author_id: str = self._to_str(response_body[2])
                ref_score_id: str | None = self._decode_ref_score_id(response_body[3])
                return VersionedDraftDocument(
                    draft_id=draft_id,
                    document=self._deserialize(revision),
                    version=version,
                    author_id=author_id,
                    ref_score_id=ref_score_id,
                )
            case "not_found":
                raise DraftNotFoundError(draft_id=draft_id)
            case _:
                raise RuntimeError(
                    f"Unexpected Redis load response: {response_code!r}, {response_body!r}."
                )

    async def commit(self, *, draft: VersionedDraftDocument) -> None:
        response: list[bytes | str | int] = await self._commit_script(
            keys=[
                self._revisions_key(draft_id=draft.draft_id),
                self._cursor_key(draft_id=draft.draft_id),
                self._version_key(draft_id=draft.draft_id),
                self._author_key(draft_id=draft.draft_id),
                self._score_key(draft_id=draft.draft_id),
            ],
            args=[
                self._serialize(draft.document),
                draft.version,
                self._MAX_DRAFT_HISTORY_SIZE,
                self._DRAFT_TTL_SECONDS,
            ],
        )

        response_code: str = self._to_str(response[0])
        response_body: list[bytes | str | int] = response[1:]

        match response_code:
            case "ok":
                return
            case "not_found":
                raise DraftNotFoundError(draft_id=draft.draft_id)
            case "version_conflict":
                raise DraftVersionClashError(draft_id=draft.draft_id, version=draft.version)
            case _:
                raise RuntimeError(
                    f"Unexpected Redis commit response: {response_code!r}, {response_body!r}."
                )

    async def undo(self, *, draft: VersionedDraftDocument) -> bool:
        response: list[bytes | str | int] = await self._undo_script(
            keys=[
                self._revisions_key(draft_id=draft.draft_id),
                self._cursor_key(draft_id=draft.draft_id),
                self._version_key(draft_id=draft.draft_id),
                self._author_key(draft_id=draft.draft_id),
                self._score_key(draft_id=draft.draft_id),
            ],
            args=[draft.version, self._DRAFT_TTL_SECONDS],
        )

        response_code: str = self._to_str(response[0])
        response_body: list[bytes | str | int] = response[1:]

        match response_code:
            case "ok":
                return True
            case "no_change":
                return False
            case "not_found":
                raise DraftNotFoundError(draft_id=draft.draft_id)
            case "version_conflict":
                raise DraftVersionClashError(draft_id=draft.draft_id, version=draft.version)
            case _:
                raise RuntimeError(
                    f"Unexpected Redis undo response: {response_code!r}, {response_body!r}."
                )

    async def redo(self, *, draft: VersionedDraftDocument) -> bool:
        response: list[bytes | str | int] = await self._redo_script(
            keys=[
                self._revisions_key(draft_id=draft.draft_id),
                self._cursor_key(draft_id=draft.draft_id),
                self._version_key(draft_id=draft.draft_id),
                self._author_key(draft_id=draft.draft_id),
                self._score_key(draft_id=draft.draft_id),
            ],
            args=[draft.version, self._DRAFT_TTL_SECONDS],
        )

        response_code: str = self._to_str(response[0])
        response_body: list[bytes | str | int] = response[1:]

        match response_code:
            case "ok":
                return True
            case "no_change":
                return False
            case "not_found":
                raise DraftNotFoundError(draft_id=draft.draft_id)
            case "version_conflict":
                raise DraftVersionClashError(draft_id=draft.draft_id, version=draft.version)
            case _:
                raise RuntimeError(
                    f"Unexpected Redis redo response: {response_code!r}, {response_body!r}."
                )

    async def hydrate(self, *, snapshot: DraftSnapshot) -> None:
        if len(snapshot.revisions) > self._MAX_DRAFT_HISTORY_SIZE:
            raise RuntimeError(f"Draft {snapshot.draft_id!r} has too many revisions.")

        response: list[bytes | str | int] = await self._hydrate_script(
            keys=[
                self._revisions_key(draft_id=snapshot.draft_id),
                self._cursor_key(draft_id=snapshot.draft_id),
                self._version_key(draft_id=snapshot.draft_id),
                self._author_key(draft_id=snapshot.draft_id),
                self._score_key(draft_id=snapshot.draft_id),
            ],
            args=[
                snapshot.cursor,
                snapshot.version,
                snapshot.author_id,
                self._encode_ref_score_id(snapshot.ref_score_id),
                self._DRAFT_TTL_SECONDS,
                *[self._serialize(revision) for revision in snapshot.revisions],
            ],
        )

        response_code: str = self._to_str(response[0])
        response_body: list[bytes | str | int] = response[1:]

        match response_code:
            case "ok" | "exists":
                return
            case _:
                raise RuntimeError(
                    f"Unexpected Redis hydrate response: {response_code!r}, {response_body!r}."
                )

    async def load_snapshot(self, *, draft_id: str) -> DraftSnapshot:
        response: list[bytes | str | int] = await self._load_snapshot_script(
            keys=[
                self._revisions_key(draft_id=draft_id),
                self._cursor_key(draft_id=draft_id),
                self._version_key(draft_id=draft_id),
                self._author_key(draft_id=draft_id),
                self._score_key(draft_id=draft_id),
            ]
        )

        response_code: str = self._to_str(response[0])
        response_body: list[bytes | str | int] = response[1:]

        match response_code:
            case "ok":
                cursor: int = int(self._to_str(response_body[0]))
                version: int = int(self._to_str(response_body[1]))
                author_id: str = self._to_str(response_body[2])
                ref_score_id: str | None = self._decode_ref_score_id(response_body[3])
                revisions: list[ScoreDocument] = [
                    self._deserialize(self._to_str(response_body[i]))
                    for i in range(4, len(response_body))
                ]

                return DraftSnapshot.create(
                    draft_id=draft_id,
                    author_id=author_id,
                    ref_score_id=ref_score_id,
                    revisions=revisions,
                    cursor=cursor,
                    version=version,
                )
            case "not_found":
                raise DraftNotFoundError(draft_id=draft_id)
            case _:
                raise RuntimeError(
                    f"Unexpected Redis load snapshot response: "
                    f"{response_code!r}, {response_body!r}."
                )

    async def aclose(self) -> None:
        """Closes the underlying Redis connection pool. Call on app shutdown."""
        await self._client.aclose()

    # the method is used to guarantee independence from the config of Redis
    # even if decode is set to False, this method guarantees that the result is always a string
    @staticmethod
    def _to_str(value: bytes | str | int) -> str:
        return value.decode() if isinstance(value, bytes) else str(value)

    def _serialize(self, document: ScoreDocument) -> str:
        return json.dumps(self._codec.serialize(document))

    def _deserialize(self, revision: str) -> ScoreDocument:
        return self._codec.deserialize(json.loads(revision))

    @classmethod
    def _encode_ref_score_id(cls, ref_score_id: str | None) -> str:
        return ref_score_id if ref_score_id is not None else _NO_SCORE_SENTINEL

    def _decode_ref_score_id(self, value: bytes | str | int) -> str | None:
        raw: str = self._to_str(value)
        return raw if raw != _NO_SCORE_SENTINEL else None

    @staticmethod
    def _revisions_key(*, draft_id: str) -> str:
        return f"draft:{draft_id}:revisions"

    @staticmethod
    def _cursor_key(*, draft_id: str) -> str:
        return f"draft:{draft_id}:cursor"

    @staticmethod
    def _version_key(*, draft_id: str) -> str:
        return f"draft:{draft_id}:version"

    @staticmethod
    def _author_key(*, draft_id: str) -> str:
        return f"draft:{draft_id}:author"

    @staticmethod
    def _score_key(*, draft_id: str) -> str:
        return f"draft:{draft_id}:score"
