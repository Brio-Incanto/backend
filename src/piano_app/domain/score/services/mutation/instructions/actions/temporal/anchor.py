from collections.abc import Hashable
from dataclasses import dataclass

from piano_app.domain.score.models.structural import (
    Measure,
    MeasurePosition,
    TemporalAnchor,
)
from piano_app.domain.score.services.mutation.instructions.actions import CreateMutationAction
from piano_app.domain.score.services.mutation.instructions.actions.base import (
    DeleteMutationAction,
)
from piano_app.domain.score.services.mutation.instructions.identity import (
    AnchorIdentity,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class CreateTemporalAnchorAction(CreateMutationAction[TemporalAnchor]):
    """Creates a temporal anchor at a position in a measure.

    Its slot ``(measure, position)`` is its identity — see ``AnchorIdentity``,
    the single source of the key so create and delete of one anchor match.
    """

    measure: Measure
    position: MeasurePosition

    @property
    def identity_key(self) -> tuple[type[TemporalAnchor], Hashable]:
        identity: AnchorIdentity = AnchorIdentity(measure=self.measure, position=self.position)
        return TemporalAnchor, identity.key


@dataclass(frozen=True, slots=True, kw_only=True)
class DeleteTemporalAnchorAction(DeleteMutationAction[TemporalAnchor]):
    """Removes a temporal anchor from its measure.

    Keyed by the same ``AnchorIdentity`` as the create, so a delete in one pass
    and a refill in the next resolve to the same slot. Produces nothing.
    """

    @property
    def identity_key(self) -> tuple[type[TemporalAnchor], Hashable]:
        return TemporalAnchor, AnchorIdentity.of(self.target).key
