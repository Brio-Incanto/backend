from collections.abc import Hashable
from dataclasses import dataclass

from piano_app.domain.score.models.structural import (
    Measure,
    MeasurePosition,
    TemporalAnchor,
)
from piano_app.domain.score.services.mutation.instructions.identity import (
    AnchorIdentity,
)
from piano_app.domain.score.services.mutation.instructions.refs import ResultRef
from piano_app.domain.score.services.mutation.instructions.requests.base import (
    MutationRequest,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class CreateTemporalAnchorRequest(MutationRequest):
    """Find-or-create the anchor at a slot. Keyed by ``AnchorIdentity`` so the
    scope interns it once across the run; the ref is published through ``out``."""

    measure: Measure
    position: MeasurePosition

    out: ResultRef[TemporalAnchor]

    @property
    def produced_ref(self) -> ResultRef[TemporalAnchor]:
        return self.out

    @property
    def identity_key(self) -> tuple[type[TemporalAnchor], Hashable]:
        identity: AnchorIdentity = AnchorIdentity(measure=self.measure, position=self.position)
        return TemporalAnchor, identity.key


@dataclass(frozen=True, slots=True, kw_only=True)
class DeleteTemporalAnchorRequest(MutationRequest):
    """Remove an anchor. Keyed by the same ``AnchorIdentity`` as the create."""

    temporal_anchor: TemporalAnchor

    @property
    def identity_key(self) -> tuple[type[TemporalAnchor], Hashable]:
        return TemporalAnchor, AnchorIdentity.of(self.temporal_anchor).key
