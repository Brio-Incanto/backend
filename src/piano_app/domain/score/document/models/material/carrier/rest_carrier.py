from dataclasses import dataclass
from typing import TYPE_CHECKING

from piano_app.domain.score.document.models.mutation_sink import DIRECT_SINK, MutationSink

from .base import Carrier

if TYPE_CHECKING:
    from piano_app.domain.score.document.models.material.carrier_owner import CarrierOwner
    from piano_app.domain.score.document.models.material.primitive.rest import Rest


@dataclass(slots=True, kw_only=True, eq=False)
class RestCarrier(Carrier):
    _rest: Rest | None = None

    @property
    def rest(self) -> Rest | None:
        return self._rest

    @classmethod
    def create(
        cls,
        *,
        owner: CarrierOwner,
        sink: MutationSink = DIRECT_SINK,
    ) -> RestCarrier:
        carrier: RestCarrier = cls(
            _owner=owner,
        )

        carrier.attach(sink=sink)
        return carrier

    @classmethod
    def reconstruct(
        cls,
        *,
        id: str,
        owner: CarrierOwner,
        sink: MutationSink = DIRECT_SINK,
    ) -> RestCarrier:
        carrier: RestCarrier = cls(
            id=id,
            _owner=owner,
        )

        carrier.attach(sink=sink)
        return carrier

    def attach_rest(
        self,
        *,
        rest: Rest,
        sink: MutationSink = DIRECT_SINK,
    ) -> None:
        if rest.rest_carrier is not self:
            raise ValueError("Cannot attach rest that belongs to another carrier.")

        if self._rest is rest:
            return

        if self._rest is not None:
            raise ValueError("Cannot attach rest because carrier already has a rest.")

        sink.set_field(self, "_rest", rest)

    def detach_rest(
        self,
        *,
        rest: Rest,
        sink: MutationSink = DIRECT_SINK,
    ) -> None:
        if rest.rest_carrier is not self:
            raise ValueError("Cannot detach rest that belongs to another carrier.")

        if self._rest is None:
            return

        if self._rest is not rest:
            raise ValueError("Cannot detach rest because carrier does not have this rest.")

        sink.set_field(self, "_rest", None)
