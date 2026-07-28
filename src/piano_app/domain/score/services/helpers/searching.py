from piano_app.domain.score.models.structural import Measure, MeasurePosition, TemporalAnchor, Voice
from piano_app.domain.score.models.structural.rhythm import LeafRhythmicContainer
from piano_app.domain.score.services.helpers import voice_of


# TODO decide if raise for multiple
def find_anchor_at(
    *,
    measure: Measure,
    position: MeasurePosition,
) -> TemporalAnchor | None:
    return next(
        (anchor for anchor in measure.anchors if anchor.position == position),
        None,
    )


def find_leaf_of_voice_at_anchor(
    *,
    anchor: TemporalAnchor | None,
    voice: Voice,
) -> LeafRhythmicContainer | None:
    return (
        next(
            (leaf for leaf in anchor.leaf_containers if voice_of(leaf) is voice),
            None,
        )
        if anchor is not None
        else None
    )


def find_leaf_at(
    *,
    measure: Measure,
    position: MeasurePosition,
    voice: Voice,
) -> LeafRhythmicContainer | None:
    return find_leaf_of_voice_at_anchor(
        anchor=find_anchor_at(measure=measure, position=position),
        voice=voice,
    )


def find_carrier_at(
    *,
    measure: Measure,
    position: MeasurePosition,
    voice: Voice,
) -> LeafRhythmicContainer | None:
    leaf: LeafRhythmicContainer | None = find_leaf_at(
        measure=measure, position=position, voice=voice
    )
    return leaf.carrier if leaf is not None else None
