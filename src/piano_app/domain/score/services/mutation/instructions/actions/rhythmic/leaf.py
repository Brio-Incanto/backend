from dataclasses import dataclass

from piano_app.domain.score.models.notation import RhythmicSize
from piano_app.domain.score.models.structural import TemporalAnchor, Voice
from piano_app.domain.score.models.structural.rhythm.metric import LeafRhythmicContainer
from piano_app.domain.score.models.structural.rhythm.metric.parent import (
    RhythmicContainerParent,
)
from piano_app.domain.score.services.mutation.instructions.actions.base import CreateMutationAction
from piano_app.domain.score.services.mutation.instructions.refs import Bound


@dataclass(frozen=True, slots=True, kw_only=True)
class CreateLeafAction(CreateMutationAction[LeafRhythmicContainer]):
    """Creates a leaf rhythmic container in a voice at an anchor.

    ``anchor`` (and an optional ``parent`` group) may be existing or produced
    earlier in the plan; the leaf is published through ``out``.
    """

    anchor: Bound[TemporalAnchor]
    voice: Voice
    written_size: RhythmicSize
    occupied_size: RhythmicSize
    parent: Bound[RhythmicContainerParent]
