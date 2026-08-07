class ResultRef[T]:
    """Symbolic handle to an entity produced during execution."""


type Bound[T] = T | ResultRef[T]
"""An action input: an already-existing entity, or a promise of a future one."""
