"""Keyset pagination: where to resume, and the opaque cursor carrying that position.

The cursor holds a value rather than a row reference, so deleting the row it points at
does not break the walk. It does not record which ordering or filter produced it —
clients reset it when either changes (docs/catalog-plan.md)."""

import base64
import binascii
import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Final

from sqlalchemy import ColumnElement, literal, true, tuple_

from piano_app.application.ports.shared.pagination import InvalidCursorError

from .ordering import NEWEST, Order


@dataclass(frozen=True, slots=True, kw_only=True)
class Keyset[T]:
    """Keyset mechanics for one ordering and its cursor representation."""

    order: Order[T]
    serialize: Callable[[T], str]
    deserialize: Callable[[str], T]

    def seek(self, *, cursor: str | None) -> ColumnElement[bool]:
        """Where the previous page stopped, or no restriction on the first page."""
        if cursor is None:
            return true()

        try:
            payload: object = json.loads(
                base64.b64decode(
                    cursor.encode(),
                    altchars=b"-_",
                    validate=True,
                )
            )

            match payload:
                case {"value": str(raw_value), "identity": str(identity)}:
                    value: T = self.deserialize(raw_value)
                case _:
                    raise TypeError("Invalid cursor payload.")
        except (
            binascii.Error,
            UnicodeDecodeError,
            ValueError,
            TypeError,
        ) as error:
            raise InvalidCursorError from error

        row: ColumnElement[tuple[T, str]] = tuple_(
            self.order.criterion,
            self.order.identity,
        )
        position: ColumnElement[tuple[T, str]] = tuple_(
            literal(value),
            literal(identity),
        )

        if self.order.descending:
            return row < position

        return row > position

    def encode(self, *, value: T, identity: str) -> str:
        payload: str = json.dumps(
            {
                "value": self.serialize(value),
                "identity": identity,
            },
            separators=(",", ":"),
        )

        return base64.urlsafe_b64encode(payload.encode()).decode()


NEWEST_PAGE: Final[Keyset[datetime]] = Keyset(
    order=NEWEST,
    serialize=lambda value: value.isoformat(),
    deserialize=datetime.fromisoformat,
)
