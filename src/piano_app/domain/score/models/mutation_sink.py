from typing import Any, Protocol


class MutationSink(Protocol):
    """Port through which domain entities perform reversible mutations.

    Domain mutators never touch their collections or fields directly; they
    route every change through a sink. The default sink applies changes in
    place and records nothing; the mutation service passes a journaling sink so
    the same changes become undoable. The domain depends only on this port —
    never on the journal or the mutation service.
    """

    def set_field(self, obj: object, name: str, value: object) -> None: ...

    def list_append(self, target: list[Any], item: Any) -> None: ...

    def list_insert(self, target: list[Any], index: int, item: Any) -> None: ...

    def list_remove(self, target: list[Any], item: Any) -> None: ...


class _DirectMutationSink:
    """Applies mutations immediately, recording nothing (no undo)."""

    def set_field(self, obj: object, name: str, value: object) -> None:
        setattr(obj, name, value)

    def list_append(self, target: list[Any], item: Any) -> None:
        target.append(item)

    def list_insert(self, target: list[Any], index: int, item: Any) -> None:
        target.insert(index, item)

    def list_remove(self, target: list[Any], item: Any) -> None:
        target.remove(item)


DIRECT_SINK: MutationSink = _DirectMutationSink()
