from dataclasses import dataclass

from piano_app.domain.score.models.context.elements.base import ContextElement
from piano_app.domain.score.models.notation import DynamicMarking


@dataclass(slots=True, kw_only=True, eq=False)
class VoicesPointContextElement(ContextElement):
    pass


@dataclass(slots=True, kw_only=True, eq=False)
class DynamicChange(VoicesPointContextElement):
    dynamic: DynamicMarking
