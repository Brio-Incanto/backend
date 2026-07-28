from collections.abc import Sequence
from dataclasses import dataclass

from piano_app.domain.score.models.material.carrier import Carrier
from piano_app.domain.score.models.mutation_sink import DIRECT_SINK, MutationSink

from .carrier import CarrierGroupRelation


@dataclass(slots=True, kw_only=True, eq=False)
class Beam(CarrierGroupRelation[Carrier]):
    """A beam over two or more ordered rhythmic carriers."""

    @classmethod
    def create(
        cls,
        *,
        carriers: Sequence[Carrier],
        sink: MutationSink = DIRECT_SINK,
    ) -> Beam:
        beam: Beam = cls(_members=tuple(carriers))
        beam.attach(sink=sink)
        return beam
