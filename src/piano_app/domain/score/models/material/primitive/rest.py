from dataclasses import dataclass

from .staff_element import StaffElement


@dataclass(frozen=True, slots=True, kw_only=True)
class Rest(StaffElement):
    pass
