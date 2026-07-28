from dataclasses import dataclass, field
from typing import Final
from uuid import uuid4


# TODO consider custom id gen mechanism
@dataclass(slots=True, kw_only=True, eq=False)
class ScoreEntity:
    id: Final[str] = field(default_factory=lambda: uuid4().hex)
