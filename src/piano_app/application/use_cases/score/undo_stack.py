from collections import deque

from piano_app.domain.score.services.mutation.engine.log import MutationLog

_STACK_CAPACITY: int = 10

class UndoStack:
    """A bounded stack of mutation journals. Beyond ``capacity`` the oldest
    journal is dropped (those mutations become permanent)."""

    def __init__(self, *, capacity: int = _STACK_CAPACITY) -> None:
        self._logs: deque[MutationLog] = deque(maxlen=capacity)

    def push(self, log: MutationLog) -> None:
        self._logs.append(log)

    def undo(self) -> bool:
        """Roll back the most recent mutation. Returns ``False`` if empty."""
        if not self._logs:
            return False

        self._logs.pop().rollback()
        return True

    def __len__(self) -> int:
        return len(self._logs)
