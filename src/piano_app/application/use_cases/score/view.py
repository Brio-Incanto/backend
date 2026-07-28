from fractions import Fraction

from piano_app.domain.score.models import ScoreDocument
from piano_app.domain.score.models.material import Carrier, NoteCarrier, RestCarrier
from piano_app.domain.score.models.material.primitive import MusicalItem, Note, Rest
from piano_app.domain.score.models.notation import DottedRhythmicValue, RhythmicSize
from piano_app.domain.score.models.relations import Relation
from piano_app.domain.score.models.relations.group import Beam
from piano_app.domain.score.models.relations.start_end import Tie
from piano_app.domain.score.models.structural import Measure, Staff, Voice
from piano_app.domain.score.models.structural.rhythm import (
    GroupRhythmicContainer,
    LeafRhythmicContainer,
    RhythmicContainer,
)


class ScoreEditView:
    def __init__(self, *, document: ScoreDocument) -> None:
        self._staffs: list[Staff] = list(document.staffs)
        self._measures: list[Measure] = list(document.measures)
        self._voices: list[Voice] = list(document.voices)

        self._rhythmic_containers: list[RhythmicContainer] = []
        self._carriers: list[Carrier] = []
        self._items: list[MusicalItem] = []
        self._relations: dict[str, Relation] = {}

        for voice in self._voices:
            for container in voice.children:
                self._collect(container=container)

    def jsonify(self) -> dict[str, object]:
        return {
            "staffs": [self._staff_json(staff=staff) for staff in self._staffs],
            "measures": [self._measure_json(measure=measure) for measure in self._measures],
            "voices": [self._voice_json(voice=voice) for voice in self._voices],
            "rhythmic_containers": [
                self._rhythmic_container_json(container=container)
                for container in self._rhythmic_containers
            ],
            "carriers": [self._carrier_json(carrier=carrier) for carrier in self._carriers],
            "items": [self._item_json(item=item) for item in self._items],
            "relations": [
                self._relation_json(relation=relation) for relation in self._relations.values()
            ],
        }

    def _collect(self, *, container: RhythmicContainer) -> None:
        self._rhythmic_containers.append(container)

        if isinstance(container, GroupRhythmicContainer):
            for child in container.children:
                self._collect(container=child)

        elif isinstance(container, LeafRhythmicContainer):
            carrier: Carrier = self._carrier_of(leaf=container)
            self._carriers.append(carrier)
            self._items.extend(self._items_of(carrier=carrier))

            for relation in self._relations_of(carrier=carrier):
                self._relations.setdefault(relation.id, relation)

        else:
            raise TypeError(f"Unsupported rhythmic container type: {type(container).__name__}.")

    def _staff_json(self, *, staff: Staff) -> dict[str, object]:
        return {"id": staff.id}

    def _measure_json(self, *, measure: Measure) -> dict[str, object]:
        return {
            "id": measure.id,
            "time_signature": self._rhythmic_size_json(size=measure.time_signature),
        }

    def _voice_json(self, *, voice: Voice) -> dict[str, object]:
        return {
            "id": voice.id,
            "rhythmic_container_ids": [container.id for container in voice.children],
        }

    def _rhythmic_container_json(
        self,
        *,
        container: RhythmicContainer,
    ) -> dict[str, object]:
        common: dict[str, object] = {
            "id": container.id,
            "written_size": self._rhythmic_size_json(size=container.written_size),
            "occupied_size": self._rhythmic_size_json(size=container.occupied_size),
        }

        if isinstance(container, GroupRhythmicContainer):
            return common | {
                "kind": "group",
                "child_ids": [child.id for child in container.children],
            }

        if isinstance(container, LeafRhythmicContainer):
            carrier: Carrier = self._carrier_of(leaf=container)
            return common | {
                "kind": "leaf",
                "measure_id": container.anchor.measure.id,
                "position": self._fraction_json(value=container.anchor.position.value),
                "carrier_id": carrier.id,
            }

        raise TypeError(f"Unsupported rhythmic container type: {type(container).__name__}.")

    def _carrier_json(self, *, carrier: Carrier) -> dict[str, object]:
        common: dict[str, object] = {
            "id": carrier.id,
        }

        if isinstance(carrier, NoteCarrier):
            return common | {
                "kind": "chord",
                "articulation": carrier.articulation.value,
                "note_ids": [note.id for note in carrier.notes],
            }

        if isinstance(carrier, RestCarrier):
            rest: Rest = self._rest_of(carrier=carrier)
            return common | {
                "kind": "rest",
                "rest_id": rest.id,
            }

        raise TypeError(f"Unsupported carrier type: {type(carrier).__name__}.")

    def _item_json(self, *, item: MusicalItem) -> dict[str, object]:
        common: dict[str, object] = {
            "id": item.id,
            "staff_id": item.staff.id,
            "staff_step": item.staff_step,
        }

        if isinstance(item, Note):
            return common | {
                "kind": "note",
                "accidental": item.accidental.value,
                "fingering": int(item.fingering),
            }

        if isinstance(item, Rest):
            return common | {
                "kind": "rest",
            }

        raise TypeError(f"Unsupported musical item type: {type(item).__name__}.")

    def _relation_json(self, *, relation: Relation) -> dict[str, object]:
        common: dict[str, object] = {
            "id": relation.id,
        }

        if isinstance(relation, Tie):
            return common | {
                "kind": "tie",
                "start_note_id": relation.start.id,
                "end_note_id": relation.end.id,
            }

        if isinstance(relation, Beam):
            return common | {
                "kind": "beam",
                "carrier_ids": [carrier.id for carrier in relation.members],
            }

        raise TypeError(f"Unsupported relation type: {type(relation).__name__}.")

    def _items_of(self, *, carrier: Carrier) -> list[MusicalItem]:
        if isinstance(carrier, NoteCarrier):
            return list(carrier.notes)

        if isinstance(carrier, RestCarrier):
            return [self._rest_of(carrier=carrier)]

        raise TypeError(f"Unsupported carrier type: {type(carrier).__name__}.")

    def _relations_of(self, *, carrier: Carrier) -> list[Relation]:
        relations: list[Relation] = list(carrier.carrier_group_relations)

        if isinstance(carrier, RestCarrier):
            return relations

        if isinstance(carrier, NoteCarrier):
            relations.extend(carrier.note_carrier_group_relations)
            for note in carrier.notes:
                relations.extend(note.relations)

            return relations

        raise TypeError(f"Unsupported carrier type: {type(carrier).__name__}.")

    def _carrier_of(self, *, leaf: LeafRhythmicContainer) -> Carrier:
        carrier: Carrier | None = leaf.carrier
        if carrier is None:
            raise RuntimeError(f"Cannot build score view: leaf {leaf.id!r} has no carrier.")

        return carrier

    def _rest_of(self, *, carrier: RestCarrier) -> Rest:
        rest: Rest | None = carrier.rest
        if rest is None:
            raise RuntimeError(f"Cannot build score view: rest carrier {carrier.id!r} has no rest.")

        return rest

    def _rhythmic_size_json(self, *, size: RhythmicSize) -> dict[str, object]:
        value: DottedRhythmicValue = size.value
        return {
            "count": size.count,
            "value": int(value.value),
            "dots": value.dots_count,
        }

    def _fraction_json(self, *, value: Fraction) -> dict[str, object]:
        return {
            "numerator": value.numerator,
            "denominator": value.denominator,
        }
