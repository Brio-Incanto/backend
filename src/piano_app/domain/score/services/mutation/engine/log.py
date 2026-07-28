from dataclasses import dataclass
from typing import Any, Protocol


class JournalEntry(Protocol):
    def undo(self) -> None: ...


@dataclass(slots=True)
class _SetField:
    obj: object
    name: str
    old: object

    def undo(self) -> None:
        setattr(self.obj, self.name, self.old)


@dataclass(slots=True)
class _ListInsert:
    target: list[Any]
    index: int

    def undo(self) -> None:
        del self.target[self.index]


@dataclass(slots=True)
class _ListRemove:
    target: list[Any]
    index: int
    item: Any

    def undo(self) -> None:
        self.target.insert(self.index, self.item)


class MutationLog:
    """Append-only journal of state-changing primitives.

    Handlers route every mutation through these primitives, so each change is
    reversible by construction (each entry captures the inverse, not just the
    fact that something happened). ``rollback`` replays the journal backwards;
    on success the caller keeps the log and pushes it onto the undo stack.

    The three primitives compose the higher-level domain operations:
    attach/detach are just list inserts/removes, edits are field sets.
    """

    def __init__(self) -> None:
        self._entries: list[JournalEntry] = []

    def set_field(self, obj: object, name: str, value: object) -> None:
        self._entries.append(_SetField(obj=obj, name=name, old=getattr(obj, name)))
        setattr(obj, name, value)

    def list_append(self, target: list[Any], item: Any) -> None:
        self._entries.append(_ListInsert(target=target, index=len(target)))
        target.append(item)

    def list_insert(self, target: list[Any], index: int, item: Any) -> None:
        self._entries.append(_ListInsert(target=target, index=index))
        target.insert(index, item)

    def list_remove(self, target: list[Any], item: Any) -> None:
        index: int = target.index(item)
        self._entries.append(_ListRemove(target=target, index=index, item=item))
        del target[index]

    def rollback(self) -> None:
        for entry in reversed(self._entries):
            entry.undo()

        self._entries.clear()
