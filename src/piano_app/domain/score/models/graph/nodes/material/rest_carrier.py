from dataclasses import dataclass

from .base_carrier import Carrier


@dataclass(frozen=True, slots=True, kw_only=True)
class RestCarrier(Carrier):
    pass
