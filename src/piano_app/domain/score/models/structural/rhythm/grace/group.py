from dataclasses import dataclass

from piano_app.domain.score.models.notation import GraceType

from .item import GraceItem


@dataclass(slots=True, kw_only=True)
class GraceGroup:
    grace_type: GraceType
    items: list[GraceItem]

    def __post_init__(self):
        if not self.items:
            raise ValueError("GraceGroup must contain at least one item.")

    # add a better ordering for items
