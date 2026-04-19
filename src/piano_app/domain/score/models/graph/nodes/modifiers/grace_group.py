from dataclasses import dataclass

from piano_app.domain.score.models.graph.notation import GraceType

from .base import ModifierNode


@dataclass(frozen=True, slots=True, kw_only=True)
class GraceGroup(ModifierNode):
    grace_type: GraceType
