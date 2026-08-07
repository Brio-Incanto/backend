from dataclasses import dataclass

from piano_app.domain.score.document.models.notation import RhythmicSize
from piano_app.domain.score.document.models.structural import TemporalAnchor
from piano_app.domain.score.document.models.structural.rhythm import (
    LeafRhythmicContainer,
    RhythmicContainerParent,
)
from piano_app.domain.score.document.services.mutation.instructions.actions.base import (
    CreateMutationAction,
    DeleteMutationAction,
)
from piano_app.domain.score.document.services.mutation.instructions.refs import Bound


@dataclass(frozen=True, slots=True, kw_only=True)
class CreateLeafAction(CreateMutationAction[LeafRhythmicContainer]):
    """Creates a leaf rhythmic container under a parent, at an anchor."""

    parent: Bound[RhythmicContainerParent]
    anchor: Bound[TemporalAnchor]
    size: RhythmicSize


@dataclass(frozen=True, slots=True, kw_only=True)
class DeleteLeafAction(DeleteMutationAction[LeafRhythmicContainer]):
    """Deletes a leaf rhythmic container."""
