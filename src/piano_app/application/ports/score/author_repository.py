from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True, kw_only=True)
class AuthorProfile:
    id: str
    username: str
    bio: str | None


class AuthorRepository(Protocol):
    async def get(self, *, author_id: str) -> AuthorProfile | None: ...
