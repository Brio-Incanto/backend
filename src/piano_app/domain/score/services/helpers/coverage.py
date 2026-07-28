from dataclasses import dataclass

from piano_app.domain.score.models.structural import Voice
from piano_app.domain.score.models.structural.rhythm.metric import (
    GroupRhythmicContainer,
)
from piano_app.domain.score.services.rhythmic_size.primitives.interval import Interval


@dataclass(slots=True, kw_only=True, eq=False)
class Coverage:
    """A rhythmic space projected as buckets — uniform for a voice and a group.

    A space holds one or more **buckets** (bounded regions the tiling rule
    applies to: a non-empty bucket must be fully covered, an empty one sleeps).
    A voice is many buckets (its measures, on the global timeline) — some may be
    empty. A group is exactly one bucket (its whole interior, in local
    coordinates) — and, while it exists, that bucket is full. ``covered`` are the
    children's footprints in the space's own coordinates; ``children`` are the
    nested group spaces to descend into.
    """

    scope: Voice | GroupRhythmicContainer
    covered: list[Interval]
    buckets: list[Interval]
    children: list[Coverage]

    @property
    def gaps(self) -> list[Interval]:
        """Every uncovered interval in this space, bucket by bucket, in local
        coordinates — purely structural and identical for a voice and a group.

        Whether a given hole is actually rest-filled is a SEPARATE policy decision
        (a wholly-empty voice measure is left to sleep; an empty group is tiled),
        applied by the fill pass, not here — so the geometry stays uniform."""
        holes: list[Interval] = []
        for bucket in self.buckets:
            holes.extend(bucket.subtract_many(self.covered))

        return holes
