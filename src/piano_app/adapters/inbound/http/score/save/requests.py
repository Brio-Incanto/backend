from pydantic import BaseModel, Field

from piano_app.application.contracts.score import CreateScoreCommand


class CreateScoreRequest(BaseModel):
    is_public: bool = Field(default=False, description="Whether the score should be public")
    title: str = Field(description="The score's title")
    composer: str | None = Field(default=None, description="The score's composer")

    def to_command(self) -> CreateScoreCommand:
        return CreateScoreCommand(
            is_public=self.is_public, title=self.title, composer=self.composer
        )
