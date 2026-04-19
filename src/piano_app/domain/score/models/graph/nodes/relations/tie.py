from dataclasses import dataclass

from .base import RelationNode


@dataclass(frozen=True, slots=True, kw_only=True)
class Tie(RelationNode):
    pass
