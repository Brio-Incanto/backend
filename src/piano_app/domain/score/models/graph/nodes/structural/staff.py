from dataclasses import dataclass

from .base import StructuralNode


@dataclass(frozen=True, slots=True, kw_only=True)
class Staff(StructuralNode):
    index: int
