from dataclasses import dataclass

from piano_app.domain.score.models.graph.notation import DynamicMarking

from .base import ContextNode


@dataclass(frozen=True, slots=True, kw_only=True)
class DynamicChange(ContextNode):
    dynamic: DynamicMarking
