from dataclasses import dataclass

from piano_app.domain.score.models.graph import Edge, Node
from piano_app.domain.score.services.graph_service import GraphService


@dataclass(frozen=True, slots=True, kw_only=True)
class DeletionContext:
    node: Node
    outgoing_edges: list[Edge]
    incoming_edges: list[Edge]
    graph_service: GraphService  # search for a more elegant way to do this
