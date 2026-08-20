import base64
import binascii
import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import Self

from sqlalchemy import ColumnElement, SQLColumnExpression, UnaryExpression, literal, true, tuple_

from piano_app.application.ports import PaginationCursorDecodingError


@dataclass(frozen=True, slots=True, kw_only=True)
class _PageKey[T]:
    """An ordering value and its unique tie-breaker carried by a cursor."""

    value: T
    identity: str


@dataclass(frozen=True, slots=True, kw_only=True)
class _Order[T]:
    """SQL expressions and direction defining a total order."""

    criterion: SQLColumnExpression[T]
    identity: SQLColumnExpression[str]
    descending: bool

    def resume_from(self, *, key: _PageKey[T]) -> ColumnElement[bool]:
        current = tuple_(
            self.criterion,
            self.identity,
        )
        boundary = tuple_(
            literal(key.value),
            literal(key.identity),
        )

        if self.descending:
            return current < boundary

        return current > boundary

    def clauses(self) -> tuple[UnaryExpression[T], UnaryExpression[str]]:
        """Return ORDER BY expressions in the configured direction."""
        if self.descending:
            return self.criterion.desc(), self.identity.desc()

        return self.criterion.asc(), self.identity.asc()


@dataclass(frozen=True, slots=True, kw_only=True)
class _CursorCodec[T]:
    """Encode and decode the opaque cursor representation of a page key."""

    serialize: Callable[[T], str]
    deserialize: Callable[[str], T]

    def decode(self, *, cursor: str) -> _PageKey[T]:
        """Decode and validate a cursor into its page key."""
        try:
            payload: object = json.loads(base64.urlsafe_b64decode(cursor))

            # structural match
            match payload:
                case {"value": str(raw_value), "identity": str(identity)}:
                    value: T = self.deserialize(raw_value)
                case _:
                    raise TypeError("Invalid cursor payload.")
        except (
            binascii.Error,  # Malformed Base64 cursor
            UnicodeDecodeError,  # Decoded payload is not valid text
            ValueError,  # Invalid JSON or serialized order value
            TypeError,  # Payload has an unexpected structure
        ) as error:
            raise PaginationCursorDecodingError from error

        return _PageKey(value=value, identity=identity)

    def encode(self, *, page_key: _PageKey[T]) -> str:
        """Encode an ordering value and identity as a URL-safe cursor."""
        payload: str = json.dumps(
            {
                "value": self.serialize(page_key.value),
                "identity": page_key.identity,
            },
        )

        return base64.urlsafe_b64encode(payload.encode()).decode()


@dataclass(frozen=True, slots=True, kw_only=True)
class CursorOrdering[T]:
    """A cursor-based pagination strategy."""

    _keyset: _CursorCodec[T]
    _order: _Order[T]

    @classmethod
    def create(
        cls,
        *,
        criterion: SQLColumnExpression[T],
        identity: SQLColumnExpression[str],
        descending: bool,
        serialize: Callable[[T], str],
        deserialize: Callable[[str], T],
    ) -> Self:
        """Create a strategy from matching SQL ordering and cursor codecs."""
        return cls(
            _keyset=_CursorCodec(
                serialize=serialize,
                deserialize=deserialize,
            ),
            _order=_Order(
                criterion=criterion,
                identity=identity,
                descending=descending,
            ),
        )

    def columns(self) -> tuple[SQLColumnExpression[T], SQLColumnExpression[str]]:
        """Return the cursor projection to append to a paginated SELECT."""
        return self._order.criterion, self._order.identity

    def clauses(self) -> tuple[UnaryExpression[T], UnaryExpression[str]]:
        """Return ORDER BY expressions matching the cursor boundary."""
        return self._order.clauses()

    def cursor_for(self, *, value: T, identity: str) -> str:
        """Encode a cursor from the cursor projection of a result row."""
        return self._keyset.encode(
            page_key=_PageKey(
                value=value,
                identity=identity,
            )
        )

    def bounds(self, *, cursor: str | None) -> ColumnElement[bool]:
        """Return the cursor boundary, or no restriction for the first page."""
        if cursor is None:
            return true()

        return self._order.resume_from(key=self._keyset.decode(cursor=cursor))
