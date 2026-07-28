from dataclasses import dataclass

from piano_app.application.contracts.score import (
    InsertNoteCommand,
    PositionInput,
    RhythmicValueInput,
)
from piano_app.domain.score.models import ScoreDocument
from piano_app.domain.score.models.notation import (
    DottedRhythmicValue,
    RhythmicSize,
    RhythmicValue,
)
from piano_app.domain.score.models.structural import Measure, Staff, Voice
from piano_app.domain.score.services.mutation.compiler import MutationCompiler
from piano_app.domain.score.services.mutation.engine import MutationEngine

_STAFF_COUNT: int = 2
_VOICE_COUNT: int = 2
_MEASURE_COUNT: int = 12
_CONTENT_BARS: int = 8


@dataclass(frozen=True, slots=True, kw_only=True)
class _SeedNote:
    """A note to insert into the seed: which measure/staff/voice, where, and how big."""

    measure: int
    staff: int
    voice: int
    numerator: int
    denominator: int
    value: RhythmicValue
    step: int


# Seed content: several fully-tiled 4/4 bars across both voices/staffs, with notes on
# ledger lines above (upper) and below (lower) to exercise ledger drawing; the rest of
# the bars stay empty (sleeping). Each pattern tiles a full 4/4 bar. Steps are the
# clef-independent staff geometry (0 = the staff's bottom line).
_Q = RhythmicValue.QUARTER
_H = RhythmicValue.HALF
_W = RhythmicValue.WHOLE
_E = RhythmicValue.EIGHTH

# a bar pattern: (numerator, denominator, value, staff_step) tuples that tile 4/4
_BarPattern = tuple[tuple[int, int, RhythmicValue, int], ...]

_UPPER_PATTERNS: tuple[_BarPattern, ...] = (
    ((0, 1, _Q, 4), (1, 4, _Q, 6), (1, 2, _Q, 8), (3, 4, _Q, 10)),
    ((0, 1, _E, 2), (1, 8, _E, 4), (1, 4, _Q, 7), (1, 2, _H, 9)),
    ((0, 1, _H, 5), (1, 2, _Q, 3), (3, 4, _Q, 1)),
)
_LOWER_PATTERNS: tuple[_BarPattern, ...] = (
    ((0, 1, _H, -2), (1, 2, _H, -4)),
    ((0, 1, _W, -6),),
    ((0, 1, _Q, 0), (1, 4, _Q, -2), (1, 2, _H, -4)),
)


def _seed_notes() -> list[_SeedNote]:
    notes: list[_SeedNote] = []

    def add(bar: int, staff: int, voice: int, pattern: _BarPattern) -> None:
        for numerator, denominator, value, step in pattern:
            notes.append(
                _SeedNote(
                    measure=bar,
                    staff=staff,
                    voice=voice,
                    numerator=numerator,
                    denominator=denominator,
                    value=value,
                    step=step,
                )
            )

    for bar in range(_CONTENT_BARS):
        add(bar, 0, 0, _UPPER_PATTERNS[bar % len(_UPPER_PATTERNS)])
        add(bar, 1, 1, _LOWER_PATTERNS[bar % len(_LOWER_PATTERNS)])

    return notes


def build_seed_document(*, engine: MutationEngine, compiler: MutationCompiler) -> ScoreDocument:
    """A blank grand staff (2 staves, 2 voices, 5 empty 4/4 bars) seeded with a couple
    of full bars of notes across both voices and staves.

    The structure is built with the direct sink; the notes are inserted through the
    engine so tiling stays correct (fill posts the remaining rests). Untouched bars
    sleep until edited.
    """
    staffs: list[Staff] = [Staff() for _ in range(_STAFF_COUNT)]
    voices: list[Voice] = [Voice() for _ in range(_VOICE_COUNT)]

    four_four: RhythmicSize = RhythmicSize(
        value=DottedRhythmicValue(value=RhythmicValue.QUARTER),
        count=4,
    )

    document: ScoreDocument = ScoreDocument.create(voices=voices, measures=[], staffs=staffs)
    for _ in range(_MEASURE_COUNT):
        document.append_measure(measure=Measure.create(time_signature=four_four))

    measures: list[Measure] = list(document.measures)
    for seed_note in _seed_notes():
        requests = compiler.compile_insert_note(
            document=document,
            intent=InsertNoteCommand(
                voice_id=voices[seed_note.voice].id,
                staff_id=staffs[seed_note.staff].id,
                measure_id=measures[seed_note.measure].id,
                position=PositionInput(
                    numerator=seed_note.numerator,
                    denominator=seed_note.denominator,
                ),
                written_value=RhythmicValueInput(value=seed_note.value.value),
                staff_step=seed_note.step,
            ),
        )
        engine.process(document=document, requests=requests)

    return document
