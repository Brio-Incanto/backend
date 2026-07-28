from dataclasses import dataclass
from typing import TYPE_CHECKING

from piano_app.domain.score.models.context.elements.span import (
    ScoreSpanContextElement,
    StaffSpanContextElement,
    VoicesSpanContextElement,
)

from .base import ContextPlacement

if TYPE_CHECKING:
    from piano_app.domain.score.models.structural import Staff, TemporalAnchor, Voice


@dataclass(slots=True, kw_only=True, eq=False)
class SpanContextPlacement(ContextPlacement):
    start: TemporalAnchor
    end: TemporalAnchor


@dataclass(slots=True, kw_only=True, eq=False)
class ScoreSpanContextPlacement(SpanContextPlacement):
    element: ScoreSpanContextElement


@dataclass(slots=True, kw_only=True, eq=False)
class StaffSpanContextPlacement(SpanContextPlacement):
    element: StaffSpanContextElement
    staff: Staff


@dataclass(slots=True, kw_only=True, eq=False)
class VoicesSpanContextPlacement(SpanContextPlacement):
    element: VoicesSpanContextElement
    voices: list[Voice]
