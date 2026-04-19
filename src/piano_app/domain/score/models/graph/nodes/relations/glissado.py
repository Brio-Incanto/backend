from dataclasses import dataclass

from piano_app.domain.score.models.graph.notation import GlissandoType

from .base import RelationNode


@dataclass(frozen=True, slots=True, kw_only=True)
class Glissando(RelationNode):
    glissando_type: GlissandoType
