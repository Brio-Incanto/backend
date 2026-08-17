from pydantic import BaseModel, Field

from piano_app.application.use_cases.score.shared import ScoreView


class ScoreEditedResponse(BaseModel):
    document: dict[str, object] = Field(description="The new document view")

    @classmethod
    def from_view(cls, view: ScoreView) -> ScoreEditedResponse:
        return cls(document=view.jsonify())
