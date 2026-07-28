from collections import deque

from piano_app.domain.score.services.mutation.engine.log import MutationLog

_STACK_CAPACITY: int = 100


class UndoRedoStack:
    """Bounded undo + redo journals for one draft.

    When a new gesture is recorded, it is pushed onto the undo stack and the redo stack is cleared.
    When a gesture is undone, it is removed from the undo stack and added to the redo stack.
    When a gesture is redone, it is removed from the redo stack and added to the undo stack.
    """

    def __init__(self, *, capacity: int = _STACK_CAPACITY) -> None:
        self._undo: deque[MutationLog] = deque(maxlen=capacity)
        self._redo: deque[MutationLog] = deque(maxlen=capacity)

    def push(self, log: MutationLog) -> None:
        self._undo.append(log)
        self._redo.clear()

    def undo(self) -> bool:
        """Rollback the most recent gesture.
        Returns ``False`` if the undo stack is empty.
        """
        if not self._undo:
            return False

        log: MutationLog = self._undo.pop()
        log.rollback()
        self._redo.append(log)
        return True

    def redo(self) -> bool:
        """Reapply the most recently undone gesture.
        Returns ``False`` if the redo stack is empty.
        """
        if not self._redo:
            return False

        log: MutationLog = self._redo.pop()
        log.reapply()
        self._undo.append(log)
        return True
