from dataclasses import dataclass

from piano_app.domain.score.models.graph import Node


@dataclass(frozen=True, slots=True, kw_only=True)
class StaffElement(Node):
    """
    Staff step index:
    0 is the first line,
    1 is the first gap above it,
    -1 is the gap below the first line.
    """

    staff_step: int
