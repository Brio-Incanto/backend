from collections.abc import Callable
from typing import Final

from pydantic import BaseModel

from piano_app.application.ports import Page

DEFAULT_LIMIT: Final[int] = 20
MAX_LIMIT: Final[int] = 100


class PageResponse[T](BaseModel):
    """The uniform envelope for every keyset-paginated listing. ``next_cursor`` is
    an opaque token to pass back as ``?cursor=`` for the next page, or ``null`` on
    the last page."""

    items: list[T]
    next_cursor: str | None

    @classmethod
    def of[S](cls, page: Page[S], *, item: Callable[[S], T]) -> PageResponse[T]:
        """Build the envelope from a domain ``Page``: map each item (pass the
        item's own ``from_x`` classmethod, e.g. ``ScoreCardResponse.from_item``)
        and carry ``next_cursor`` through, so no router repeats it or drops it."""
        return cls(
            items=[item(element) for element in page.items],
            next_cursor=page.next_cursor,
        )
