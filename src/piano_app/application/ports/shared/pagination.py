from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True, slots=True, kw_only=True)
class Page[T]:
    """One page of a keyset-paginated listing. ``next_cursor`` is an opaque token
    to pass back for the next page, or ``None`` when the last page was returned."""

    items: Sequence[T]
    next_cursor: str | None


class PaginationCursorDecodingError(Exception):
    """Raised when an opaque pagination cursor cannot be decoded."""
