from dataclasses import dataclass

from piano_app.domain.score.models.graph.notation import HairpinType

from .base import RelationNode


@dataclass(frozen=True, slots=True, kw_only=True)
class Hairpin(RelationNode):
    hairpin_type: HairpinType
