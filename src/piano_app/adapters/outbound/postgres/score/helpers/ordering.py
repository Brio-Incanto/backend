from dataclasses import dataclass
from datetime import datetime
from typing import Final

from sqlalchemy import SQLColumnExpression, UnaryExpression

from piano_app.adapters.outbound.postgres.schema.core import ScoreMetaORM


@dataclass(frozen=True, slots=True, kw_only=True)
class Order[T]:
    """A criterion together with the unique column that breaks ties on it — paging needs
    both, so they travel as one value rather than by agreement between call sites.

    ``criterion`` is any SQL expression, so a stored column and a ranking computed per
    request work alike; it must be NOT NULL, since a NULL compares as UNKNOWN and would
    drop the row out of keyset pagination."""

    criterion: SQLColumnExpression[T]
    identity: SQLColumnExpression[str]
    descending: bool

    def clauses(self) -> tuple[UnaryExpression[T], UnaryExpression[str]]:
        """ORDER BY. Both columns run the same way because ``seek`` compares them as a
        single row value."""
        if self.descending:
            return self.criterion.desc(), self.identity.desc()

        return self.criterion.asc(), self.identity.asc()


NEWEST: Final[Order[datetime]] = Order(
    criterion=ScoreMetaORM.created_at,
    identity=ScoreMetaORM.id,
    descending=True,
)
