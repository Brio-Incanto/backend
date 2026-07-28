from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from piano_app.domain.score.models.material.carrier import Carrier
    from piano_app.domain.score.models.mutation_sink import MutationSink


class CarrierOwner(Protocol):
    """A score entity that can own a single carrier — a metric leaf or a grace
    item.

    Carriers attach to and detach from their owner through this contract, so
    ``Carrier`` depends on the capability, not on the concrete owner types.
    Code that must distinguish leaf from grace still narrows with ``isinstance``
    against the concrete classes.
    """

    carrier: Carrier | None

    def attach_carrier(self, *, carrier: Carrier, sink: MutationSink) -> None: ...

    def detach_carrier(self, *, carrier: Carrier, sink: MutationSink) -> None: ...
