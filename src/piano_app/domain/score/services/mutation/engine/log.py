from dataclasses import dataclass
from typing import Any, Protocol


class _JournalEntry(Protocol):
    def apply(self) -> None: ...  # redo: re-do the forward change

    def undo(self) -> None: ...  # undo: revert to the previous state


@dataclass(slots=True, kw_only=True)
class _SetField:
    target: object
    field_name: str
    previous_value: object
    new_value: object

    def apply(self) -> None:
        setattr(self.target, self.field_name, self.new_value)

    def undo(self) -> None:
        setattr(self.target, self.field_name, self.previous_value)


@dataclass(slots=True, kw_only=True)
class _ListInsert:
    target: list[Any]
    index: int
    item: Any

    def apply(self) -> None:
        self.target.insert(self.index, self.item)

    def undo(self) -> None:
        del self.target[self.index]


@dataclass(slots=True, kw_only=True)
class _ListRemove:
    target: list[Any]
    index: int
    item: Any

    def apply(self) -> None:
        del self.target[self.index]

    def undo(self) -> None:
        self.target.insert(self.index, self.item)


class MutationLog:
    """Append-only journal of state-changing primitives — reversible AND re-appliable.

    Each entry captures both directions: ``undo`` reverts to the previous state and
    ``apply`` re-does the forward change. So one journal serves three roles: the
    gesture's inverse (transaction abort / user undo) and its replay (redo), and, in
    time, the delta between two saved revisions. Handlers route every mutation through
    these primitives, so attach/detach are list inserts/removes and edits are field sets.
    """

    def __init__(self) -> None:
        self._entries: list[_JournalEntry] = []

    def set_field(self, target: object, field_name: str, value: object) -> None:
        entry: _SetField = _SetField(
            target=target,
            field_name=field_name,
            previous_value=getattr(target, field_name),
            new_value=value,
        )
        entry.apply()
        self._entries.append(entry)

    def list_append(self, target: list[Any], item: Any) -> None:
        entry: _ListInsert = _ListInsert(target=target, index=len(target), item=item)
        entry.apply()
        self._entries.append(entry)

    def list_insert(self, target: list[Any], index: int, item: Any) -> None:
        entry: _ListInsert = _ListInsert(target=target, index=index, item=item)
        entry.apply()
        self._entries.append(entry)

    def list_remove(self, target: list[Any], item: Any) -> None:
        index: int = target.index(item)
        entry: _ListRemove = _ListRemove(target=target, index=index, item=item)
        entry.apply()
        self._entries.append(entry)

    def rollback(self) -> None:
        """Revert the journal (one gesture). Replay every entry's ``undo`` in reverse order.

        Used for a transaction abort (the failed gesture is then dropped) and for user
        undo (the journal is kept and moves to the redo stack).
        """
        for entry in reversed(self._entries):
            entry.undo()

    def reapply(self) -> None:
        """Re-do the journal (one gesture). Replay every entry's ``apply`` in original order."""
        for entry in self._entries:
            entry.apply()
