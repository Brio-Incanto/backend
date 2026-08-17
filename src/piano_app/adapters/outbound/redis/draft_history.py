import json
from typing import Final
from uuid import uuid4

from redis.asyncio import Redis
from redis.commands.core import AsyncScript

from piano_app.adapters.outbound.shared.codec import ScoreDocumentCodec
from piano_app.application.ports.score.draft_store import (
    DraftNotFoundError,
    DraftVersionClashError,
    VersionedDraftDocument,
)
from piano_app.domain.score.document import ScoreDocument

from .shared_lua_scripts import _COMMIT_SCRIPT, _LOAD_SCRIPT, _REDO_SCRIPT, _UNDO_SCRIPT

# ref_score_id (str | None) has no native null over the Redis string protocol, so
# an absent score is written as this sentinel rather than leaving the key missing —
# keeps every script's EXISTS-count check flat (all 5 keys always present) instead
# of combinatorial once more optional fields show up. Real score ids are always
# server-generated UUIDs (ScoreORM.id / DraftORM.id both server_default=
# gen_random_uuid()), so collision is not just unlikely but structurally impossible.
# TODO: revisit the storage mechanism for optional draft fields if this pattern needs
# to repeat for a second optional field (e.g. a Redis HASH with native missing-field
# semantics instead of per-field sentinels) — considered now, deferred as overkill
# for a single field with a collision-proof sentinel.
_NO_SCORE_SENTINEL: Final[str] = "none"

# own to RedisDraftHistory only (RedisDraftCache has no create()); load/commit/undo/redo
# are identical hot-tier mechanics shared by both, imported from .shared_lua_scripts.
# arguments are expected to be validated by the caller
_CREATE_SCRIPT: str = """
local revisions_key = KEYS[1]
local cursor_key = KEYS[2]
local version_key = KEYS[3]
local author_key = KEYS[4]
local score_key = KEYS[5]

local author_id = ARGV[1]
local score_id = ARGV[2]
local new_revision = ARGV[3]
local ttl_seconds = ARGV[4]
local initial_version = 0

local keys_count = redis.call(
    'EXISTS', revisions_key, cursor_key, version_key, author_key, score_key
)
if keys_count == 5 then
    return {'exists'}
end
if keys_count ~= 0 then
    return {'corrupt', 'partial_keys'}
end

redis.call('RPUSH', revisions_key, new_revision)
redis.call('SET', cursor_key, 0)
redis.call('SET', version_key, initial_version)
redis.call('SET', author_key, author_id)
redis.call('SET', score_key, score_id)

redis.call('EXPIRE', revisions_key, ttl_seconds)
redis.call('EXPIRE', cursor_key, ttl_seconds)
redis.call('EXPIRE', version_key, ttl_seconds)
redis.call('EXPIRE', author_key, ttl_seconds)
redis.call('EXPIRE', score_key, ttl_seconds)

return {'ok', initial_version}
"""


class RedisDraftHistory:
    """Redis-backed draft history.

    For each draft there are five keys: revisions (``draft:{id}:revisions``),
    cursor (``draft:{id}:cursor``), monotonically increasing version
    (``draft:{id}:version``), author (``draft:{id}:author``), and the score it
    derives from, if any (``draft:{id}:score``, may hold the sentinel — see
    ``_NO_SCORE_SENTINEL``). Lua scripts update them atomically.
    """

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
        self._create_script: AsyncScript = client.register_script(_CREATE_SCRIPT)
        self._commit_script: AsyncScript = client.register_script(_COMMIT_SCRIPT)
        self._undo_script: AsyncScript = client.register_script(_UNDO_SCRIPT)
        self._redo_script: AsyncScript = client.register_script(_REDO_SCRIPT)

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

    async def create(
        self,
        *,
        author_id: str,
        ref_score_id: str | None,
        document: ScoreDocument,
    ) -> VersionedDraftDocument:
        while True:
            draft_id: str = str(uuid4())
            response: list[bytes | str | int] = await self._create_script(
                keys=[
                    self._revisions_key(draft_id=draft_id),
                    self._cursor_key(draft_id=draft_id),
                    self._version_key(draft_id=draft_id),
                    self._author_key(draft_id=draft_id),
                    self._score_key(draft_id=draft_id),
                ],
                args=[
                    author_id,
                    self._encode_ref_score_id(ref_score_id),
                    self._serialize(document),
                    self._DRAFT_TTL_SECONDS,
                ],
            )

            response_code: str = self._to_str(response[0])
            response_body: list[bytes | str | int] = response[1:]

            match response_code:
                case "ok":
                    initial_version: int = int(self._to_str(response_body[0]))
                    return VersionedDraftDocument(
                        draft_id=draft_id,
                        document=document,
                        version=initial_version,
                        author_id=author_id,
                        ref_score_id=ref_score_id,
                    )
                case "exists":
                    continue
                case _:
                    raise RuntimeError(
                        f"Unexpected Redis create response: {response_code!r}, {response_body!r}."
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
