from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True, slots=True, kw_only=True)
class PositionInput:
    numerator: int
    denominator: int


@dataclass(frozen=True, slots=True, kw_only=True)
class RhythmicValueInput:
    value: int
    dots: int = 0


@dataclass(frozen=True, slots=True, kw_only=True)
class InsertNoteCommand:
    voice_id: str
    staff_id: str
    measure_id: str
    position: PositionInput
    written_value: RhythmicValueInput
    staff_step: int
    accidental: str = "none"
    fingering: int = 0


@dataclass(frozen=True, slots=True, kw_only=True)
class TieNotesCommand:
    start_note_id: str
    end_note_id: str


@dataclass(frozen=True, slots=True, kw_only=True)
class DeleteBatchCommand:
    entity_ids: Sequence[str]
