from dataclasses import dataclass

from piano_app.domain.score.models.graph.notation import ArpeggioType

from .base import RelationNode


@dataclass(frozen=True, slots=True, kw_only=True)
class Arpeggio(RelationNode):
    arpeggio_type: ArpeggioType = ArpeggioType.ARPEGGIATO
