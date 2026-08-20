from collections.abc import Sequence
from copy import deepcopy
from dataclasses import replace
from datetime import UTC, datetime
from typing import Final
from uuid import uuid4

from piano_app.application.ports.score import (
    DraftMeta,
    DraftStoreNotFoundError,
    DraftStoreVersionConflictError,
    VersionedDraftDocument,
)
from piano_app.domain.score.document import ScoreDocument


class _SingleDraftHistory:
    def __init__(
        self,
        *,
        meta: DraftMeta,
        initial_version: ScoreDocument,
        max_history_size: int,
    ) -> None:
        if max_history_size < 1:
            raise ValueError(f"max_history_size must be >= 1, got {max_history_size!r}.")

        self._meta: DraftMeta = meta
        self._current_version_index: int = 0
        self._draft_versions: list[ScoreDocument] = [deepcopy(initial_version)]
        self._version: int = 0

        self._MAX_DRAFT_HISTORY_SIZE: Final[int] = max_history_size

    @property
    def meta(self) -> DraftMeta:
        return self._meta

    def load(self) -> VersionedDraftDocument:
        # a fresh copy, otherwise that in-place mutation silently corrupts history underneath it
        return VersionedDraftDocument(
            meta=self._meta,
            document=deepcopy(self._draft_versions[self._current_version_index]),
            version=self._version,
        )

    def has_version(self, *, version: int) -> bool:
        return self._version == version

    def push(self, *, document: ScoreDocument) -> None:
        # cut off the versions that are left ahead beacause of undo
        self._draft_versions = self._draft_versions[: self._current_version_index + 1]

        self._draft_versions.append(deepcopy(document))
        # free up memory if max_draft_history_size is reached
        if len(self._draft_versions) > self._MAX_DRAFT_HISTORY_SIZE:
            self._draft_versions.pop(0)

        self._current_version_index = len(self._draft_versions) - 1
        self._version += 1
        self._touch()

    def undo(self) -> bool:
        if self._current_version_index <= 0:
            return False

        self._current_version_index -= 1
        self._version += 1
        self._touch()
        return True

    def redo(self) -> bool:
        if self._current_version_index >= len(self._draft_versions) - 1:
            return False

        self._current_version_index += 1
        self._version += 1
        self._touch()
        return True

    def _touch(self) -> None:
        self._meta = replace(self._meta, updated_at=datetime.now(UTC))


class InMemoryDraftHistory:
    """In-process draft history keyed by draft id."""

    def __init__(
        self,
        *,
        max_history_size: int = 30,
    ) -> None:
        if max_history_size < 1:
            raise ValueError(f"max_history_size must be >= 1, got {max_history_size!r}.")

        self._draft_histories: dict[str, _SingleDraftHistory] = {}
        self._MAX_DRAFT_HISTORY_SIZE: Final[int] = max_history_size

    def _history_for(self, *, draft_id: str) -> _SingleDraftHistory:
        history: _SingleDraftHistory | None = self._draft_histories.get(draft_id)
        if history is None:
            raise DraftStoreNotFoundError(draft_id=draft_id)

        return history

    async def create(
        self,
        *,
        title: str,
        author_id: str,
        ref_score_id: str | None,
        document: ScoreDocument,
    ) -> VersionedDraftDocument:
        draft_id: str = str(uuid4())
        while draft_id in self._draft_histories:
            draft_id = str(uuid4())

        history: _SingleDraftHistory = _SingleDraftHistory(
            meta=DraftMeta(
                draft_id=draft_id,
                title=title,
                author_id=author_id,
                ref_score_id=ref_score_id,
                updated_at=datetime.now(UTC),
            ),
            initial_version=document,
            max_history_size=self._MAX_DRAFT_HISTORY_SIZE,
        )
        self._draft_histories[draft_id] = history
        return history.load()

    async def get(self, *, draft_id: str) -> VersionedDraftDocument | None:
        history: _SingleDraftHistory | None = self._draft_histories.get(draft_id)
        return None if history is None else history.load()

    async def list_by_author(self, *, author_id: str) -> Sequence[DraftMeta]:
        matching: list[DraftMeta] = [
            history.meta
            for history in self._draft_histories.values()
            if history.meta.author_id == author_id
        ]
        return sorted(
            matching,
            key=lambda meta: (meta.updated_at, meta.draft_id),
            reverse=True,
        )

    async def commit(self, *, draft: VersionedDraftDocument) -> None:
        draft_id: str = draft.meta.draft_id
        history: _SingleDraftHistory = self._history_for(draft_id=draft_id)
        self._ensure_version(
            draft_id=draft_id,
            history=history,
            version=draft.version,
        )
        history.push(document=draft.document)

    async def undo(self, *, draft: VersionedDraftDocument) -> bool:
        draft_id: str = draft.meta.draft_id
        history: _SingleDraftHistory = self._history_for(draft_id=draft_id)
        self._ensure_version(draft_id=draft_id, history=history, version=draft.version)

        return history.undo()

    async def redo(self, *, draft: VersionedDraftDocument) -> bool:
        draft_id: str = draft.meta.draft_id
        history: _SingleDraftHistory = self._history_for(draft_id=draft_id)
        self._ensure_version(draft_id=draft_id, history=history, version=draft.version)

        return history.redo()

    @staticmethod
    def _ensure_version(
        *,
        draft_id: str,
        history: _SingleDraftHistory,
        version: int,
    ) -> None:
        if not history.has_version(version=version):
            raise DraftStoreVersionConflictError(draft_id=draft_id, version=version)
