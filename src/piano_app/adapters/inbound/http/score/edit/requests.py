from pydantic import BaseModel

from piano_app.application.contracts.score import (
    DeleteBatchCommand,
    InsertNoteCommand,
    PositionInput,
    RhythmicValueInput,
    TieNotesCommand,
)


class PositionModel(BaseModel):
    numerator: int
    denominator: int

    def to_input(self) -> PositionInput:
        return PositionInput(numerator=self.numerator, denominator=self.denominator)


class RhythmicValueModel(BaseModel):
    value: int
    dots: int = 0

    def to_input(self) -> RhythmicValueInput:
        return RhythmicValueInput(value=self.value, dots=self.dots)


class InsertNoteRequest(BaseModel):
    voice_id: str
    staff_id: str
    measure_id: str
    position: PositionModel
    written_value: RhythmicValueModel
    staff_step: int
    accidental: str = "none"
    fingering: int = 0

    def to_command(self) -> InsertNoteCommand:
        return InsertNoteCommand(
            voice_id=self.voice_id,
            staff_id=self.staff_id,
            measure_id=self.measure_id,
            position=self.position.to_input(),
            written_value=self.written_value.to_input(),
            staff_step=self.staff_step,
            accidental=self.accidental,
            fingering=self.fingering,
        )


class TieNotesRequest(BaseModel):
    start_note_id: str
    end_note_id: str

    def to_command(self) -> TieNotesCommand:
        return TieNotesCommand(start_note_id=self.start_note_id, end_note_id=self.end_note_id)


class DeleteBatchRequest(BaseModel):
    entity_ids: list[str]

    def to_command(self) -> DeleteBatchCommand:
        return DeleteBatchCommand(entity_ids=self.entity_ids)
