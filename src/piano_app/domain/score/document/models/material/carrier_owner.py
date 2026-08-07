from typing import TYPE_CHECKING, Protocol

from piano_app.domain.score.document.models.mutation_sink import DIRECT_SINK, MutationSink

if TYPE_CHECKING:
    from piano_app.domain.score.document.models.material.carrier import Carrier


class CarrierOwner(Protocol):
    """A score entity that can own a single carrier — a metric leaf or a grace
    item.

    Carriers attach to and detach from their owner through this contract, so
    ``Carrier`` depends on the capability, not on the concrete owner types.
    Code that must distinguish leaf from grace still narrows with ``isinstance``
    against the concrete classes.
    """

    # None while the owner is transiently empty — during construction, or between
    # a carrier's detach and the cleanup boundary that reaps the empty owner
    _carrier: Carrier | None

    @property
    def carrier(self) -> Carrier | None: ...

    def attach_carrier(
        self,
        *,
        carrier: Carrier,
        sink: MutationSink = DIRECT_SINK,
    ) -> None: ...

    def detach_carrier(
        self,
        *,
        carrier: Carrier,
        sink: MutationSink = DIRECT_SINK,
    ) -> None: ...
