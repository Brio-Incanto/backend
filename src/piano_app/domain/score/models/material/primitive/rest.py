from dataclasses import dataclass
from typing import TYPE_CHECKING

from piano_app.domain.score.models.mutation_sink import DIRECT_SINK, MutationSink

from .base import MusicalItem

if TYPE_CHECKING:
    from piano_app.domain.score.models.material.carrier import RestCarrier
    from piano_app.domain.score.models.structural import Staff


@dataclass(slots=True, kw_only=True, eq=False)
class Rest(MusicalItem):
    _rest_carrier: RestCarrier

    @property
    def rest_carrier(self) -> RestCarrier:
        return self._rest_carrier

    @classmethod
    def create(
        cls,
        *,
        rest_carrier: RestCarrier,
        staff: Staff,
        staff_step: int,
        sink: MutationSink = DIRECT_SINK,
    ) -> Rest:
        rest: Rest = cls(
            staff_step=staff_step,
            _staff=staff,
            _rest_carrier=rest_carrier,
        )

        rest.attach(sink=sink)
        return rest

    @classmethod
    def reconstruct(
        cls,
        *,
        id: str,
        rest_carrier: RestCarrier,
        staff: Staff,
        staff_step: int,
        sink: MutationSink = DIRECT_SINK,
    ) -> Rest:
        rest: Rest = cls(
            id=id,
            staff_step=staff_step,
            _staff=staff,
            _rest_carrier=rest_carrier,
        )

        rest.attach(sink=sink)
        return rest

    def attach(self, *, sink: MutationSink = DIRECT_SINK) -> None:
        super().attach(sink=sink)
        self._rest_carrier.attach_rest(rest=self, sink=sink)

    def detach(self, *, sink: MutationSink = DIRECT_SINK) -> None:
        self._rest_carrier.detach_rest(rest=self, sink=sink)
        super().detach(sink=sink)
