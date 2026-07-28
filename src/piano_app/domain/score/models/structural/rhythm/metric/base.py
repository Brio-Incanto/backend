from dataclasses import dataclass

from piano_app.domain.score.models.notation import RhythmicSize


@dataclass(slots=True, kw_only=True)
class RhythmicContainer:
    written_size: RhythmicSize
    occupied_size: RhythmicSize

    parent: RhythmicContainer | None = None
    # decide on parent type
