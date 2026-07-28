from fractions import Fraction
from typing import Any

from piano_app.domain.score.models import ScoreDocument
from piano_app.domain.score.models.material import Carrier, NoteCarrier, RestCarrier
from piano_app.domain.score.models.material.primitive import Note, Rest
from piano_app.domain.score.models.notation import DottedRhythmicValue, RhythmicSize
from piano_app.domain.score.models.structural import Measure
from piano_app.domain.score.models.structural.rhythm import LeafRhythmicContainer
from piano_app.domain.score.services.helpers import flatten

type ScoreEditView = dict[str, Any]
type VoiceMeasureItems = dict[str, dict[str, list[ScoreEditView]]]


def build_score_edit_view(*, document: ScoreDocument, score_id: str) -> ScoreEditView:
    buckets: VoiceMeasureItems = {}
    for voice in document.voices:
        for leaf in flatten(voice):
            item: ScoreEditView | None = _item_of(leaf)
            if item is None:
                continue

            measure_id: str = leaf.anchor.measure.id
            buckets.setdefault(voice.id, {}).setdefault(measure_id, []).append(item)

    measures: list[ScoreEditView] = []
    for measure in document.measures:
        voices: list[ScoreEditView] = []
        for voice in document.voices:
            items: list[ScoreEditView] = buckets.get(voice.id, {}).get(measure.id, [])
            if items:
                voices.append({"voice_id": voice.id, "items": items})

        measures.append(
            {
                "id": measure.id,
                "time_signature": _time_signature(measure),
                "voices": voices,
            }
        )

    return {
        "score_id": score_id,
        "staff_order": [staff.id for staff in document.staffs],
        "voices": [voice.id for voice in document.voices],
        "measures": measures,
    }


def _item_of(leaf: LeafRhythmicContainer) -> ScoreEditView | None:
    carrier: Carrier | None = leaf.carrier
    if carrier is None:
        return None

    item: ScoreEditView = {
        "carrier_id": carrier.id,
        "position": _position(leaf),
        "duration": _duration(leaf),
    }
    if isinstance(carrier, NoteCarrier):
        notes: list[Note] = list(carrier.notes)
        if not notes:
            return None
        return item | {
            "kind": "note",
            "notes": [_note(note) for note in notes],
        }

    if isinstance(carrier, RestCarrier):
        rest: Rest | None = carrier.rest
        if rest is None:
            return None
        return item | {
            "kind": "rest",
            "notes": [],
            "staff_id": rest.staff.id,
            "staff_step": rest.staff_step,
        }

    raise TypeError(f"Unsupported carrier type: {type(carrier).__name__}.")


def _note(note: Note) -> ScoreEditView:
    return {
        "note_id": note.id,
        "staff_id": note.staff.id,
        "staff_step": note.staff_step,
        "accidental": note.accidental.value,
    }


def _duration(leaf: LeafRhythmicContainer) -> ScoreEditView:
    dotted: DottedRhythmicValue = leaf.written_size.value
    return {"value": int(dotted.value), "dots": dotted.dots_count}


def _position(leaf: LeafRhythmicContainer) -> ScoreEditView:
    position: Fraction = leaf.anchor.position.value
    return {
        "numerator": position.numerator,
        "denominator": position.denominator,
    }


def _time_signature(measure: Measure) -> ScoreEditView:
    size: RhythmicSize = measure.time_signature
    return {"beats": size.count, "beat_value": int(size.value.value)}
