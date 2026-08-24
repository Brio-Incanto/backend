from piano_app.domain.score.document.models.context.point.staff import StaffPointContext
from piano_app.domain.score.document.models.structural import (
    Measure,
    MeasurePosition,
    Staff,
    TemporalAnchor,
    Voice,
)
from piano_app.domain.score.document.models.structural.rhythm import LeafRhythmicContainer
from piano_app.domain.score.document.services.helpers import voice_of

# Slot lookup: what already sits at a given place in the model. Purely a question
# about occupancy, not about coordinates -- anything that needs to measure, project
# or compare positions belongs in `services/geometry` instead.


def find_anchor_at(
    *,
    measure: Measure,
    position: MeasurePosition,
) -> TemporalAnchor | None:
    # one or None guaranteed in model
    return next(
        (anchor for anchor in measure.anchors if anchor.position == position),
        None,
    )


def find_leaf_of_voice_at_anchor(
    *,
    anchor: TemporalAnchor,
    voice: Voice,
) -> LeafRhythmicContainer | None:
    # validate only one leaf container per voice at one anchor
    leaves: list[LeafRhythmicContainer] = [
        leaf for leaf in anchor.leaf_containers if voice_of(leaf) is voice
    ]
    if len(leaves) > 1:
        raise ValueError(f"Multiple leaf containers found for voice {voice} at one anchor.")

    # return this only leaf container or None
    return leaves[0] if leaves else None


def find_leaf_at(
    *,
    measure: Measure,
    position: MeasurePosition,
    voice: Voice,
) -> LeafRhythmicContainer | None:
    anchor: TemporalAnchor | None = find_anchor_at(measure=measure, position=position)
    if anchor is None:
        return None

    return find_leaf_of_voice_at_anchor(
        anchor=anchor,
        voice=voice,
    )


def find_staff_point_context_at[T: StaffPointContext](
    *,
    anchor: TemporalAnchor,
    context_type: type[T],
    staff: Staff,
) -> T | None:
    """The context of exactly ``context_type`` already starting at this anchor, for
    this staff — the search behind the one-per-anchor-per-staff invariant. Shared by
    every ``StaffPointContext`` creator so the invariant is enforced once, not
    reimplemented per type.
    """
    return next(
        (
            context
            for context in anchor.starting_contexts
            if isinstance(context, context_type) and context.staff is staff
        ),
        None,
    )
