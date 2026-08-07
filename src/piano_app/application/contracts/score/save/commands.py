from dataclasses import dataclass


@dataclass(frozen=True, slots=True, kw_only=True)
class CreateScoreCommand:
    is_public: bool
    title: str
    composer: str | None
