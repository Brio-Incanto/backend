import json
from datetime import UTC, datetime
from typing import Final

from redis.asyncio import Redis
from redis.commands.core import AsyncScript

from piano_app.adapters.outbound.shared.codec import ScoreDocumentCodec
from piano_app.adapters.outbound.shared.draft_snapshot import DraftSnapshot
from piano_app.application.ports.score import (
    DraftStoreNotFoundError,
    DraftStoreVersionConflictError,
    VersionedDraftDocument,
)
from piano_app.domain.score.document import ScoreDocument

from .shared_lua_scripts import _COMMIT_SCRIPT, _GET_SCRIPT, _REDO_SCRIPT, _UNDO_SCRIPT, _load

# Redis hashes have no native scalar null. The `score` field is required so
# scripts can distinguish a complete draft with no referenced score from a
# corrupted meta hash missing the field. Referenced score ids are generated
# UUIDs, so they cannot collide with this sentinel.
_NO_SCORE_SENTINEL: Final[str] = "none"

# own to RedisDraftCache only (RedisDraftHistory has neither hydrate() nor
# load_snapshot()); get/commit/undo/redo are identical hot-tier mechanics shared
# by both, imported from .shared_lua_scripts.
_HYDRATE_SCRIPT: str = _load("hydrate.lua")
_LOAD_SNAPSHOT_SCRIPT: str = _load("load_snapshot.lua")


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
        # (get() is read-only and does not refresh the TTL)
        self._DRAFT_TTL_SECONDS: Final[int] = ttl_seconds

        self._get_script: AsyncScript = client.register_script(_GET_SCRIPT)
        self._commit_script: AsyncScript = client.register_script(_COMMIT_SCRIPT)
        self._undo_script: AsyncScript = client.register_script(_UNDO_SCRIPT)
        self._redo_script: AsyncScript = client.register_script(_REDO_SCRIPT)
        self._hydrate_script: AsyncScript = client.register_script(_HYDRATE_SCRIPT)
        self._load_snapshot_script: AsyncScript = client.register_script(_LOAD_SNAPSHOT_SCRIPT)

    async def get(self, *, draft_id: str) -> VersionedDraftDocument | None:
        response: list[bytes | str | int] = await self._get_script(
            keys=[
                self._revisions_key(draft_id=draft_id),
                self._state_key(draft_id=draft_id),
                self._meta_key(draft_id=draft_id),
            ]
        )

        response_code: str = self._to_str(response[0])
        response_body: list[bytes | str | int] = response[1:]

        match response_code:
            case "ok":
                document: ScoreDocument = self._deserialize(response_body[0])
                version: int = self._decode_version(response_body[1])
                author_id: str = self._to_str(response_body[2])
                title: str = self._to_str(response_body[3])
                updated_at: datetime = self._decode_datetime(response_body[4])
                ref_score_id: str | None = self._decode_ref_score_id(response_body[5])
                return VersionedDraftDocument.create(
                    draft_id=draft_id,
                    title=title,
                    author_id=author_id,
                    ref_score_id=ref_score_id,
                    updated_at=updated_at,
                    document=document,
                    version=version,
                )
            case "not_found":
                return None
            case _:
                raise RuntimeError(
                    f"Unexpected Redis get response: {response_code!r}, {response_body!r}."
                )

    async def commit(self, *, draft: VersionedDraftDocument) -> None:
        response: list[bytes | str | int] = await self._commit_script(
            keys=[
                self._revisions_key(draft_id=draft.draft_id),
                self._state_key(draft_id=draft.draft_id),
                self._meta_key(draft_id=draft.draft_id),
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
                raise DraftStoreNotFoundError(draft_id=draft.draft_id)
            case "version_conflict":
                raise DraftStoreVersionConflictError(draft_id=draft.draft_id, version=draft.version)
            case _:
                raise RuntimeError(
                    f"Unexpected Redis commit response: {response_code!r}, {response_body!r}."
                )

    async def undo(self, *, draft: VersionedDraftDocument) -> bool:
        response: list[bytes | str | int] = await self._undo_script(
            keys=[
                self._revisions_key(draft_id=draft.draft_id),
                self._state_key(draft_id=draft.draft_id),
                self._meta_key(draft_id=draft.draft_id),
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
                raise DraftStoreNotFoundError(draft_id=draft.draft_id)
            case "version_conflict":
                raise DraftStoreVersionConflictError(draft_id=draft.draft_id, version=draft.version)
            case _:
                raise RuntimeError(
                    f"Unexpected Redis undo response: {response_code!r}, {response_body!r}."
                )

    async def redo(self, *, draft: VersionedDraftDocument) -> bool:
        response: list[bytes | str | int] = await self._redo_script(
            keys=[
                self._revisions_key(draft_id=draft.draft_id),
                self._state_key(draft_id=draft.draft_id),
                self._meta_key(draft_id=draft.draft_id),
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
                raise DraftStoreNotFoundError(draft_id=draft.draft_id)
            case "version_conflict":
                raise DraftStoreVersionConflictError(draft_id=draft.draft_id, version=draft.version)
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
                self._state_key(draft_id=snapshot.draft_id),
                self._meta_key(draft_id=snapshot.draft_id),
            ],
            args=[
                snapshot.cursor,
                snapshot.version,
                snapshot.author_id,
                snapshot.title,
                self._encode_ref_score_id(snapshot.ref_score_id),
                self._encode_datetime(snapshot.updated_at),
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
                self._state_key(draft_id=draft_id),
                self._meta_key(draft_id=draft_id),
            ]
        )

        response_code: str = self._to_str(response[0])
        response_body: list[bytes | str | int] = response[1:]

        match response_code:
            case "ok":
                cursor: int = int(self._to_str(response_body[0]))
                version: int = int(self._to_str(response_body[1]))
                author_id: str = self._to_str(response_body[2])
                title: str = self._to_str(response_body[3])
                updated_at: datetime = self._decode_datetime(response_body[4])
                ref_score_id: str | None = self._decode_ref_score_id(response_body[5])
                revisions: list[ScoreDocument] = [
                    self._deserialize(self._to_str(response_body[i]))
                    for i in range(6, len(response_body))
                ]

                return DraftSnapshot.create(
                    draft_id=draft_id,
                    author_id=author_id,
                    title=title,
                    ref_score_id=ref_score_id,
                    updated_at=updated_at,
                    revisions=revisions,
                    cursor=cursor,
                    version=version,
                )
            case "not_found":
                raise DraftStoreNotFoundError(draft_id=draft_id)
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

    def _deserialize(self, value: bytes | str | int) -> ScoreDocument:
        return self._codec.deserialize(json.loads(self._to_str(value)))

    @classmethod
    def _encode_ref_score_id(cls, ref_score_id: str | None) -> str:
        return ref_score_id if ref_score_id is not None else _NO_SCORE_SENTINEL

    def _decode_ref_score_id(self, value: bytes | str | int) -> str | None:
        raw: str = self._to_str(value)
        return raw if raw != _NO_SCORE_SENTINEL else None

    def _decode_version(self, value: bytes | str | int) -> int:
        return int(self._to_str(value))

    @staticmethod
    def _encode_datetime(value: datetime) -> str:
        return str(int(value.timestamp()))

    def _decode_datetime(self, value: bytes | str | int) -> datetime:
        return datetime.fromtimestamp(
            int(self._to_str(value)),
            tz=UTC,
        )

    @staticmethod
    def _revisions_key(*, draft_id: str) -> str:
        return f"draft:{draft_id}:revisions"

    @staticmethod
    def _state_key(*, draft_id: str) -> str:
        return f"draft:{draft_id}:state"

    @staticmethod
    def _meta_key(*, draft_id: str) -> str:
        return f"draft:{draft_id}:meta"
