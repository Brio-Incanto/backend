from collections.abc import Sequence
from fractions import Fraction
from typing import Any

from piano_app.domain.score.document.models import ScoreDocument, ScoreEntity
from piano_app.domain.score.document.models.context.placements import ContextPlacement
from piano_app.domain.score.document.models.material import (
    Carrier,
    CarrierOwner,
    MusicalItem,
    Note,
    NoteCarrier,
    Rest,
    RestCarrier,
)
from piano_app.domain.score.document.models.notation import (
    Accidental,
    Articulation,
    DottedRhythmicValue,
    Fingering,
    GracePlacement,
    GraceType,
    RhythmicSize,
    RhythmicValue,
)
from piano_app.domain.score.document.models.relations import Beam, Relation, Tie
from piano_app.domain.score.document.models.structural import (
    Measure,
    MeasurePosition,
    Staff,
    TemporalAnchor,
    Voice,
)
from piano_app.domain.score.document.models.structural.rhythm import (
    GraceGroup,
    GraceItem,
    GroupRhythmicContainer,
    LeafRhythmicContainer,
    RhythmicContainer,
    RhythmicContainerParent,
)

type SerializedScoreDocument = dict[str, Any]


class _Serializer:
    def __init__(self, *, document: ScoreDocument) -> None:
        self._voices: list[Voice] = list(document.voices)
        self._staffs: list[Staff] = list(document.staffs)
        self._measures: list[Measure] = list(document.measures)
        self._anchors: dict[str, TemporalAnchor] = {}
        self._containers: dict[str, RhythmicContainer] = {}
        self._grace_groups: dict[str, GraceGroup] = {}
        self._graces: dict[str, GraceItem] = {}
        self._carriers: dict[str, Carrier] = {}
        self._items: dict[str, MusicalItem] = {}
        self._relations: dict[str, Relation] = {}
        self._contexts: list[ContextPlacement] = []  # TODO

        self._collect(document=document)

    # a plain keyed write is the dedup: registering the same entity twice
    # (reached via two different paths in the graph) is just a harmless overwrite.
    # I expect that no collisions of ids should happen, only revisiting an entity
    def _add[T: ScoreEntity](self, *, into: dict[str, T], entity: T) -> None:
        into[entity.id] = entity

    def _collect(self, *, document: ScoreDocument) -> None:
        for measure in document.measures:
            for anchor in measure.anchors:
                self._add(into=self._anchors, entity=anchor)

                # TODO collect context

                for leaf in anchor.leaf_containers:
                    hierarchy: list[RhythmicContainer] = [leaf]

                    parent: RhythmicContainerParent = leaf.parent
                    while not isinstance(parent, Voice):
                        if isinstance(parent, GroupRhythmicContainer):
                            hierarchy.append(parent)
                            parent = parent.parent
                        else:
                            raise TypeError(
                                f"Unsupported rhythmic container type: {type(parent).__name__}."
                            )

                    # in reverse order, so that top level containers are added first
                    # to be able to resolve immediately in deserialization
                    for container in reversed(hierarchy):
                        self._add(into=self._containers, entity=container)

                    grace_before: GraceGroup | None = leaf.grace_before
                    if grace_before is not None:
                        self._add(into=self._grace_groups, entity=grace_before)

                        grace_before_items: Sequence[GraceItem] = grace_before.grace_items
                        if not grace_before_items:
                            raise ValueError("Grace group must have at least one grace item.")

                        for grace_item in grace_before_items:
                            self._add(into=self._graces, entity=grace_item)

                    grace_after: GraceGroup | None = leaf.grace_after
                    if grace_after is not None:
                        self._add(into=self._grace_groups, entity=grace_after)

                        grace_after_items: Sequence[GraceItem] = grace_after.grace_items
                        if not grace_after_items:
                            raise ValueError("Grace group must have at least one grace item.")

                        for grace_item in grace_after_items:
                            self._add(into=self._graces, entity=grace_item)

                    carrier: Carrier | None = leaf.carrier
                    if carrier is None:
                        raise ValueError("Leaf must have a carrier.")

                    self._add(into=self._carriers, entity=carrier)
                    for carrier_relation in carrier.carrier_group_relations:
                        self._add(into=self._relations, entity=carrier_relation)

                    if isinstance(carrier, NoteCarrier):
                        for note_carrier_relation in carrier.note_carrier_group_relations:
                            self._add(into=self._relations, entity=note_carrier_relation)

                        if not carrier.notes:
                            raise ValueError("Note carrier must have at least one note.")

                        for note in carrier.notes:
                            self._add(into=self._items, entity=note)
                            for note_relation in note.relations:
                                self._add(into=self._relations, entity=note_relation)
                    elif isinstance(carrier, RestCarrier):
                        if carrier.rest is None:
                            raise ValueError("Rest carrier must have a rest.")

                        self._add(into=self._items, entity=carrier.rest)
                    else:
                        raise TypeError(f"Unsupported carrier type: {type(carrier).__name__}.")

    def serialize(self) -> dict[str, Any]:
        return {
            "voices": [self._serialize_voice(voice=voice) for voice in self._voices],
            "staffs": [self._serialize_staff(staff=staff) for staff in self._staffs],
            "measures": [self._serialize_measure(measure=measure) for measure in self._measures],
            "anchors": [
                self._serialize_temporal_anchor(anchor=anchor) for anchor in self._anchors.values()
            ],
            "rhythmic": [
                self._serialize_rhythmic_container(container=container)
                for container in self._containers.values()
            ],
            "grace_groups": [
                self._serialize_grace_group(group=group) for group in self._grace_groups.values()
            ],
            "grace_items": [
                self._serialize_grace_item(item=item) for item in self._graces.values()
            ],
            "carriers": [
                self._serialize_carrier(carrier=carrier) for carrier in self._carriers.values()
            ],
            "musical_items": [
                self._serialize_musical_item(item=item) for item in self._items.values()
            ],
            "relations": [
                self._serialize_relation(relation=relation) for relation in self._relations.values()
            ],
        }

    def _serialize_voice(self, *, voice: Voice) -> dict[str, Any]:
        return {
            "id": voice.id,
        }

    def _serialize_staff(self, *, staff: Staff) -> dict[str, Any]:
        return {
            "id": staff.id,
        }

    def _serialize_measure(self, *, measure: Measure) -> dict[str, Any]:
        return {
            "id": measure.id,
            **self._serialize_rhythmic_size(size=measure.time_signature, prefix="time_signature"),
        }

    def _serialize_temporal_anchor(self, *, anchor: TemporalAnchor) -> dict[str, Any]:
        return {
            "id": anchor.id,
            "measure_id": anchor.measure.id,
            **self._serialize_fraction(value=anchor.position.value, prefix="position"),
        }

    def _serialize_rhythmic_container(self, *, container: RhythmicContainer) -> dict[str, Any]:
        parent: RhythmicContainerParent = container.parent
        parent_id: str
        if isinstance(parent, (Voice, GroupRhythmicContainer)):
            parent_id = parent.id
        else:
            raise TypeError(f"Unsupported rhythmic container parent type: {type(parent).__name__}.")

        common: dict[str, Any] = {
            "id": container.id,
            "parent_id": parent_id,
            **self._serialize_rhythmic_size(size=container.written_size, prefix="written"),
            **self._serialize_rhythmic_size(size=container.occupied_size, prefix="occupied"),
        }

        if isinstance(container, LeafRhythmicContainer):
            return common | {
                "kind": "leaf",
                "anchor_id": container.anchor.id,
            }

        if isinstance(container, GroupRhythmicContainer):
            return common | {
                "kind": "group",
            }

        raise TypeError(f"Unsupported rhythmic container type: {type(container).__name__}.")

    def _serialize_grace_group(self, *, group: GraceGroup) -> dict[str, Any]:
        return {
            "id": group.id,
            "leaf_id": group.leaf.id,
            "grace_type": group.grace_type.value,
            "placement": group.placement.value,
        }

    def _serialize_grace_item(self, *, item: GraceItem) -> dict[str, Any]:
        return {
            "id": item.id,
            "grace_group_id": item.grace_group.id,
            **self._serialize_dotted_value(value=item.rhythmic_value, prefix="grace_group"),
        }

    def _serialize_carrier(self, *, carrier: Carrier) -> dict[str, Any]:
        owner: CarrierOwner | None = carrier.owner
        if owner is None:
            raise ValueError("Carrier must have an owner.")

        owner_id: str
        if isinstance(owner, (LeafRhythmicContainer, GraceItem)):
            owner_id = owner.id
        else:
            raise TypeError(f"Unsupported carrier owner type: {type(owner).__name__}.")

        common: dict[str, Any] = {
            "id": carrier.id,
            "owner_id": owner_id,
        }

        if isinstance(carrier, NoteCarrier):
            return common | {
                "kind": "note_carrier",
                "articulation": carrier.articulation.value,
            }

        if isinstance(carrier, RestCarrier):
            return common | {
                "kind": "rest_carrier",
            }

        raise TypeError(f"Unsupported carrier type: {type(carrier).__name__}.")

    def _serialize_musical_item(self, *, item: MusicalItem) -> dict[str, Any]:
        common: dict[str, Any] = {
            "id": item.id,
            "staff_id": item.staff.id,
            "staff_step": item.staff_step,
        }

        if isinstance(item, Note):
            return common | {
                "kind": "note",
                "note_carrier_id": item.note_carrier.id,
                "accidental": item.accidental.value,
                "fingering": item.fingering.value,
            }

        if isinstance(item, Rest):
            return common | {
                "kind": "rest",
                "rest_carrier_id": item.rest_carrier.id,
            }

        raise TypeError(f"Unsupported musical item type: {type(item).__name__}.")

    def _serialize_relation(self, *, relation: Relation) -> dict[str, Any]:
        common: dict[str, Any] = {
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

    def _serialize_dotted_value(self, *, value: DottedRhythmicValue, prefix: str) -> dict[str, Any]:
        return {
            f"{prefix}_value": int(value.value),
            f"{prefix}_dots": value.dots_count,
        }

    def _serialize_rhythmic_size(self, *, size: RhythmicSize, prefix: str) -> dict[str, Any]:
        return {
            **self._serialize_dotted_value(value=size.value, prefix=prefix),
            f"{prefix}_count": size.count,
        }

    def _serialize_fraction(self, *, value: Fraction, prefix: str) -> dict[str, Any]:
        return {
            f"{prefix}_numerator": value.numerator,
            f"{prefix}_denominator": value.denominator,
        }


class _Deserializer:
    """Rebuilds a ScoreDocument from `_Serializer`'s flat tables.

    Each ``_build_*`` step resolves its rows' foreign keys against the
    already-built id maps from earlier steps, then reconstructs via each
    entity's `.reconstruct()`.
    """

    def __init__(self, *, data: dict[str, Any]) -> None:
        self._data: dict[str, Any] = data

        self._voices_by_id: dict[str, Voice] = {
            row["id"]: Voice(id=row["id"]) for row in data["voices"]
        }
        self._staffs_by_id: dict[str, Staff] = {
            row["id"]: Staff(id=row["id"]) for row in data["staffs"]
        }

        self._document: ScoreDocument = ScoreDocument.create(
            voices=list(self._voices_by_id.values()),
            staffs=list(self._staffs_by_id.values()),
            measures=[],
        )

        self._measures_by_id: dict[str, Measure] = self._build_measures()
        self._anchors_by_id: dict[str, TemporalAnchor] = self._build_anchors()
        self._containers_by_id: dict[str, RhythmicContainer] = self._build_rhythmic_containers()
        self._grace_groups_by_id: dict[str, GraceGroup] = self._build_grace_groups()
        self._grace_items_by_id: dict[str, GraceItem] = self._build_grace_items()

        self._carrier_owners_by_id: dict[str, CarrierOwner] = {
            **{
                container.id: container
                for container in self._containers_by_id.values()
                if isinstance(container, LeafRhythmicContainer)
            },
            **self._grace_items_by_id,
        }
        self._carriers_by_id: dict[str, Carrier] = self._build_carriers()
        self._notes_by_id: dict[str, Note] = self._build_musical_items()
        self._build_relations()

    def deserialize(self) -> ScoreDocument:
        return self._document

    def _build_measures(self) -> dict[str, Measure]:
        by_id: dict[str, Measure] = {}
        for row in self._data["measures"]:
            measure: Measure = Measure(
                id=row["id"],
                time_signature=self._rhythmic_size(row=row, prefix="time_signature"),
            )
            self._document.append_measure(measure=measure)
            by_id[row["id"]] = measure

        return by_id

    def _build_anchors(self) -> dict[str, TemporalAnchor]:
        by_id: dict[str, TemporalAnchor] = {}
        for row in self._data["anchors"]:
            by_id[row["id"]] = TemporalAnchor.reconstruct(
                id=row["id"],
                measure=self._measures_by_id[row["measure_id"]],
                position=MeasurePosition.of_fraction(
                    fraction=self._fraction(row=row, prefix="position"),
                ),
            )

        return by_id

    def _build_rhythmic_containers(self) -> dict[str, RhythmicContainer]:
        by_id: dict[str, RhythmicContainer] = {}
        # only groups can ever be a parent, so keep them separately
        groups_by_id: dict[str, GroupRhythmicContainer] = {}
        remaining: list[dict[str, Any]] = list(self._data["rhythmic"])

        # despite serialising hierarchy in the order that allows for always hitting resolve,
        # I add additional protection by resolving in waves
        while remaining:
            unresolved: list[dict[str, Any]] = []
            for row in remaining:
                parent: RhythmicContainerParent | None = self._voices_by_id.get(
                    row["parent_id"]
                ) or groups_by_id.get(row["parent_id"])

                if parent is None:
                    unresolved.append(row)
                    continue

                container: RhythmicContainer = self._build_rhythmic_container(
                    row=row, parent=parent
                )
                by_id[row["id"]] = container
                if isinstance(container, GroupRhythmicContainer):
                    groups_by_id[row["id"]] = container

            if len(unresolved) == len(remaining):
                raise ValueError(
                    "Cannot resolve rhythmic container parents (cycle or missing parent)."
                )

            remaining = unresolved

        return by_id

    def _build_rhythmic_container(
        self,
        *,
        row: dict[str, Any],
        parent: RhythmicContainerParent,
    ) -> RhythmicContainer:
        written_size: RhythmicSize = self._rhythmic_size(row=row, prefix="written")
        occupied_size: RhythmicSize = self._rhythmic_size(row=row, prefix="occupied")

        kind: str = row["kind"]
        if kind == "leaf":
            return LeafRhythmicContainer.reconstruct(
                id=row["id"],
                parent=parent,
                anchor=self._anchors_by_id[row["anchor_id"]],
                size=written_size,
            )

        if kind == "group":
            return GroupRhythmicContainer.reconstruct(
                id=row["id"],
                parent=parent,
                written_size=written_size,
                occupied_size=occupied_size,
            )

        raise ValueError(f"Unsupported rhythmic container kind: {kind}.")

    def _build_grace_groups(self) -> dict[str, GraceGroup]:
        by_id: dict[str, GraceGroup] = {}
        for row in self._data["grace_groups"]:
            leaf: RhythmicContainer = self._containers_by_id[row["leaf_id"]]
            if not isinstance(leaf, LeafRhythmicContainer):
                raise TypeError(f"Grace group's leaf_id does not resolve to a leaf: {leaf.id!r}.")

            by_id[row["id"]] = GraceGroup.reconstruct(
                id=row["id"],
                leaf=leaf,
                grace_type=GraceType(row["grace_type"]),
                placement=GracePlacement(row["placement"]),
            )

        return by_id

    def _build_grace_items(self) -> dict[str, GraceItem]:
        by_id: dict[str, GraceItem] = {}
        for row in self._data["grace_items"]:
            by_id[row["id"]] = GraceItem.reconstruct(
                id=row["id"],
                grace_group=self._grace_groups_by_id[row["grace_group_id"]],
                rhythmic_value=DottedRhythmicValue(
                    value=RhythmicValue(row["grace_group_value"]),
                    dots_count=row["grace_group_dots"],
                ),
            )

        return by_id

    def _build_carriers(self) -> dict[str, Carrier]:
        by_id: dict[str, Carrier] = {}
        for row in self._data["carriers"]:
            owner: CarrierOwner = self._carrier_owners_by_id[row["owner_id"]]

            kind: str = row["kind"]
            if kind == "note_carrier":
                by_id[row["id"]] = NoteCarrier.reconstruct(
                    id=row["id"],
                    owner=owner,
                    articulation=Articulation(row["articulation"]),
                )
            elif kind == "rest_carrier":
                by_id[row["id"]] = RestCarrier.reconstruct(id=row["id"], owner=owner)
            else:
                raise ValueError(f"Unsupported carrier kind: {kind}.")

        return by_id

    def _build_musical_items(self) -> dict[str, Note]:
        notes_by_id: dict[str, Note] = {}
        for row in self._data["musical_items"]:
            staff: Staff = self._staffs_by_id[row["staff_id"]]

            kind: str = row["kind"]
            if kind == "note":
                note_carrier: Carrier = self._carriers_by_id[row["note_carrier_id"]]
                if not isinstance(note_carrier, NoteCarrier):
                    raise TypeError(f"Note's note_carrier_id is not a note carrier: {row['id']!r}.")

                notes_by_id[row["id"]] = Note.reconstruct(
                    id=row["id"],
                    note_carrier=note_carrier,
                    staff=staff,
                    staff_step=row["staff_step"],
                    accidental=Accidental(row["accidental"]),
                    fingering=Fingering(row["fingering"]),
                )
            elif kind == "rest":
                rest_carrier: Carrier = self._carriers_by_id[row["rest_carrier_id"]]
                if not isinstance(rest_carrier, RestCarrier):
                    raise TypeError(f"Rest's rest_carrier_id is not a rest carrier: {row['id']!r}.")

                Rest.reconstruct(
                    id=row["id"],
                    rest_carrier=rest_carrier,
                    staff=staff,
                    staff_step=row["staff_step"],
                )
            else:
                raise ValueError(f"Unsupported musical item kind: {kind}.")

        return notes_by_id

    def _build_relations(self) -> None:
        for row in self._data["relations"]:
            kind: str = row["kind"]
            if kind == "tie":
                Tie.reconstruct(
                    id=row["id"],
                    start_note=self._notes_by_id[row["start_note_id"]],
                    end_note=self._notes_by_id[row["end_note_id"]],
                )
            elif kind == "beam":
                Beam.reconstruct(
                    id=row["id"],
                    carriers=[self._carriers_by_id[cid] for cid in row["carrier_ids"]],
                )
            else:
                raise ValueError(f"Unsupported relation kind: {kind}.")

    @staticmethod
    def _rhythmic_size(*, row: dict[str, Any], prefix: str) -> RhythmicSize:
        return RhythmicSize(
            value=DottedRhythmicValue(
                value=RhythmicValue(row[f"{prefix}_value"]),
                dots_count=row[f"{prefix}_dots"],
            ),
            count=row[f"{prefix}_count"],
        )

    @staticmethod
    def _fraction(*, row: dict[str, Any], prefix: str) -> Fraction:
        return Fraction(
            numerator=row[f"{prefix}_numerator"],
            denominator=row[f"{prefix}_denominator"],
        )


class CodecError(Exception):
    def __init__(self, *, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class ScoreDocumentCodec:
    def serialize(self, document: ScoreDocument) -> SerializedScoreDocument:
        try:
            serializer: _Serializer = _Serializer(document=document)
            return serializer.serialize()
        except Exception as e:
            raise CodecError(reason=str(e)) from e

    def deserialize(self, data: SerializedScoreDocument) -> ScoreDocument:
        try:
            deserializer: _Deserializer = _Deserializer(data=data)
            return deserializer.deserialize()
        except Exception as e:
            raise CodecError(reason=str(e)) from e
