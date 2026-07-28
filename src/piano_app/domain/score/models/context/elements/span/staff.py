from dataclasses import dataclass

from piano_app.domain.score.models.context.elements.base import ContextElement


@dataclass(slots=True, kw_only=True, eq=False)
class StaffSpanContextElement(ContextElement):
    pass


@dataclass(slots=True, kw_only=True, eq=False)
class OctaveTransposition(StaffSpanContextElement):
    pass
