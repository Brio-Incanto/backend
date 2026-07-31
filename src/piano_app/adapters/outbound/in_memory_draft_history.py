from copy import deepcopy

from piano_app.application.ports.draft_store import DraftNotFoundError
from piano_app.domain.score.models import ScoreDocument

MAX_DRAFT_HISTORY_SIZE: int = 30


class _SingleDraftHistory:
    def __init__(self, *, initial_version: ScoreDocument) -> None:
        self._current_version_index: int = 0
        self._draft_versions: list[ScoreDocument] = [initial_version]

    def load(self) -> ScoreDocument:
        # a fresh copy, otherwise that in-place mutation silently corrupts history underneath it
        return deepcopy(self._draft_versions[self._current_version_index])

    def push(self, *, document: ScoreDocument) -> None:
        # cut off the versions that are left ahead beacause of undo
        self._draft_versions = self._draft_versions[: self._current_version_index + 1]

        self._draft_versions.append(deepcopy(document))
        # free up memory if max_draft_history_size is reached
        if len(self._draft_versions) > MAX_DRAFT_HISTORY_SIZE:
            self._draft_versions.pop(0)

        self._current_version_index += 1

    def undo(self) -> bool:
        if self._current_version_index <= 0:
            return False

        self._current_version_index -= 1
        return True

    def redo(self) -> bool:
        if self._current_version_index >= len(self._draft_versions) - 1:
            return False

        self._current_version_index += 1
        return True


class InMemoryDraftHistory:
    """In-process draft history keyed by draft id."""

    def __init__(self, *, drafts: dict[str, ScoreDocument] | None = None) -> None:
        self._draft_histories: dict[str, _SingleDraftHistory] = {}

        for draft_id, draft in (drafts or {}).items():
            self._draft_histories[draft_id] = _SingleDraftHistory(initial_version=draft)

    def _history_for(self, *, draft_id: str) -> _SingleDraftHistory:
        history: _SingleDraftHistory | None = self._draft_histories.get(draft_id)
        if history is None:
            raise DraftNotFoundError(draft_id=draft_id)

        return history

    async def load(self, *, draft_id: str) -> ScoreDocument:
        return self._history_for(draft_id=draft_id).load()

    async def commit(self, *, draft_id: str, document: ScoreDocument) -> None:
        self._history_for(draft_id=draft_id).push(document=document)

    async def undo(self, *, draft_id: str) -> bool:
        return self._history_for(draft_id=draft_id).undo()

    async def redo(self, *, draft_id: str) -> bool:
        return self._history_for(draft_id=draft_id).redo()
