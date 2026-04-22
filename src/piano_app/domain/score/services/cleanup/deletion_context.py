from dataclasses import dataclass

from piano_app.domain.score.models.graph import Edge, Node


@dataclass(frozen=True, slots=True, kw_only=True)
class DeletionContext:
    node: Node
    outgoing_edges: list[Edge]
    incoming_edges: list[Edge]
