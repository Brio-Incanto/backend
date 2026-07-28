import itertools
from dataclasses import dataclass, field

_ref_ids = itertools.count()


@dataclass(frozen=True, slots=True)
class ResultRef[T]:
    """Symbolic handle to an entity produced during execution.

    Identity is per-instance (a unique id), so two distinct producers never
    collide even when they create structurally equal entities. The executor
    resolves a ref to a concrete entity through its run-time environment once
    the producing action has run.

    The parameter is phantom (carries the produced type for static checking
    only) and unused in the body, so it is variance-flexible: a
    ``ResultRef[Subtype]`` is usable where a ``ResultRef[Supertype]`` is
    expected (e.g. a leaf ref as a ``CarrierOwner`` ref) — sound because a ref
    is a read-only handle.
    """

    id: int = field(default_factory=lambda: next(_ref_ids))


type Bound[T] = T | ResultRef[T]
"""An action input: an already-existing entity, or a promise of a future one."""
