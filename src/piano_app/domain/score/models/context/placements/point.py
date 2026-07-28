from dataclasses import dataclass
from typing import TYPE_CHECKING

from piano_app.domain.score.models.context.elements.point import (
    ScorePointContextElement,
    StaffPointContextElement,
    VoicesPointContextElement,
)

from .base import ContextPlacement

if TYPE_CHECKING:
    from piano_app.domain.score.models.structural import Staff, TemporalAnchor, Voice


@dataclass(slots=True, kw_only=True, eq=False)
class PointContextPlacement(ContextPlacement):
    start: TemporalAnchor


@dataclass(slots=True, kw_only=True, eq=False)
class ScorePointContextPlacement(PointContextPlacement):
    element: ScorePointContextElement


@dataclass(slots=True, kw_only=True, eq=False)
class StaffPointContextPlacement(PointContextPlacement):
    element: StaffPointContextElement
    staff: Staff


@dataclass(slots=True, kw_only=True, eq=False)
class VoicesPointContextPlacement(PointContextPlacement):
    element: VoicesPointContextElement
    voices: list[Voice]
