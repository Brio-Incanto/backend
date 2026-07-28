from collections.abc import Sequence
from typing import Protocol


class PositionIntent(Protocol):
    @property
    def numerator(self) -> int: ...

    @property
    def denominator(self) -> int: ...


class RhythmicValueIntent(Protocol):
    @property
    def value(self) -> int: ...

    @property
    def dots(self) -> int: ...


class InsertNoteIntent(Protocol):
    @property
    def voice_id(self) -> str: ...

    @property
    def staff_id(self) -> str: ...

    @property
    def measure_id(self) -> str: ...

    @property
    def position(self) -> PositionIntent: ...

    @property
    def written_value(self) -> RhythmicValueIntent: ...

    @property
    def staff_step(self) -> int: ...

    @property
    def accidental(self) -> str: ...

    @property
    def fingering(self) -> int: ...


class DeleteBatchIntent(Protocol):
    @property
    def entity_ids(self) -> Sequence[str]: ...
