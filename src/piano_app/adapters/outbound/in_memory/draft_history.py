from copy import deepcopy
from typing import Final
from uuid import uuid4

from piano_app.application.ports.score.draft_store import (
    DraftNotFoundError,
    DraftVersionClashError,
    VersionedDraftDocument,
)
from piano_app.domain.score.document import ScoreDocument


class _SingleDraftHistory:
    def __init__(
        self,
        *,
        draft_id: str,
        author_id: str,
        ref_score_id: str | None,
        initial_version: ScoreDocument,
        max_history_size: int,
    ) -> None:
        if max_history_size < 1:
            raise ValueError(f"max_history_size must be >= 1, got {max_history_size!r}.")

        self._draft_id: str = draft_id
        self._current_version_index: int = 0
        self._draft_versions: list[ScoreDocument] = [deepcopy(initial_version)]
        self._version: int = 0
        self._author_id: str = author_id
        self._ref_score_id: str | None = ref_score_id

        self._MAX_DRAFT_HISTORY_SIZE: Final[int] = max_history_size

    def load(self) -> VersionedDraftDocument:
        # a fresh copy, otherwise that in-place mutation silently corrupts history underneath it
        return VersionedDraftDocument(
            draft_id=self._draft_id,
            document=deepcopy(self._draft_versions[self._current_version_index]),
            version=self._version,
            author_id=self._author_id,
            ref_score_id=self._ref_score_id,
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

    def undo(self) -> bool:
        if self._current_version_index <= 0:
            return False

        self._current_version_index -= 1
        self._version += 1
        return True

    def redo(self) -> bool:
        if self._current_version_index >= len(self._draft_versions) - 1:
            return False

        self._current_version_index += 1
        self._version += 1
        return True


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
            raise DraftNotFoundError(draft_id=draft_id)

        return history

    async def create(
        self,
        *,
        author_id: str,
        ref_score_id: str | None,
        document: ScoreDocument,
    ) -> VersionedDraftDocument:
        draft_id: str = str(uuid4())
        while draft_id in self._draft_histories:
            draft_id = str(uuid4())

        history: _SingleDraftHistory = _SingleDraftHistory(
            draft_id=draft_id,
            author_id=author_id,
            ref_score_id=ref_score_id,
            initial_version=document,
            max_history_size=self._MAX_DRAFT_HISTORY_SIZE,
        )
        self._draft_histories[draft_id] = history
        return history.load()

    async def load(self, *, draft_id: str) -> VersionedDraftDocument:
        return self._history_for(draft_id=draft_id).load()

    async def commit(self, *, draft: VersionedDraftDocument) -> None:
        history: _SingleDraftHistory = self._history_for(draft_id=draft.draft_id)
        self._ensure_version(
            draft_id=draft.draft_id,
            history=history,
            version=draft.version,
        )
        history.push(document=draft.document)

    async def undo(self, *, draft: VersionedDraftDocument) -> bool:
        history: _SingleDraftHistory = self._history_for(draft_id=draft.draft_id)
        self._ensure_version(draft_id=draft.draft_id, history=history, version=draft.version)
        return history.undo()

    async def redo(self, *, draft: VersionedDraftDocument) -> bool:
        history: _SingleDraftHistory = self._history_for(draft_id=draft.draft_id)
        self._ensure_version(draft_id=draft.draft_id, history=history, version=draft.version)
        return history.redo()

    @staticmethod
    def _ensure_version(
        *,
        draft_id: str,
        history: _SingleDraftHistory,
        version: int,
    ) -> None:
        if not history.has_version(version=version):
            raise DraftVersionClashError(draft_id=draft_id, version=version)
