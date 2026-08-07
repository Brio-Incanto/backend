from dataclasses import dataclass

from piano_app.domain.score.document.models.context.elements.base import ContextElement


@dataclass(slots=True, kw_only=True, eq=False)
class ScoreSpanContextElement(ContextElement):
    pass


@dataclass(slots=True, kw_only=True, eq=False)
class SustainHold(ScoreSpanContextElement):
    pass
