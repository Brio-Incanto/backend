from dataclasses import dataclass

from piano_app.domain.score.models.graph import Node


@dataclass(frozen=True, slots=True, kw_only=True)
class DeleteRequest:
    node: Node
