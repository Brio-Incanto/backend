from dataclasses import dataclass

from piano_app.domain.score.models.graph.node import Node


@dataclass(frozen=True, slots=True, kw_only=True)
class RelationNode(Node):
    pass
