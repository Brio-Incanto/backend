from dataclasses import dataclass

from piano_app.domain.score.models.graph.node import Node
from piano_app.domain.score.models.graph.notation import Accidental, Fingering


@dataclass(frozen=True, slots=True, kw_only=True)
class Note(Node):
    """
    Staff step index:
    0 is the first line,
    1 is the first gap above it,
    -1 is the gap below the first line.
    """

    staff_step: int
    accidental: Accidental = Accidental.NONE
    fingering: Fingering = Fingering.NONE
