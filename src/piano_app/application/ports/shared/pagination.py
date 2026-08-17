from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True, slots=True, kw_only=True)
class Page[T]:
    """One page of a keyset-paginated listing. ``next_cursor`` is an opaque token
    to pass back for the next page, or ``None`` when the last page was returned."""

    items: Sequence[T]
    next_cursor: str | None


class InvalidCursorError(Exception):
    """Raised when a client-supplied pagination cursor cannot be decoded."""

    def __init__(self) -> None:
        super().__init__("Pagination cursor is invalid.")
