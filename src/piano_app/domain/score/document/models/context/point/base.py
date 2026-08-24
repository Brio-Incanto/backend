from dataclasses import dataclass

from piano_app.domain.shared.abstract import abstract

from ..base import Context


@abstract
@dataclass(slots=True, kw_only=True, eq=False)
class PointContext(Context):
    """A context that occupies a single instant — ``start`` is inherited as-is,
    there is nothing extra to place."""
