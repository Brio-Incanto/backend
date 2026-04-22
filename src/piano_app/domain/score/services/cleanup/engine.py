from collections import deque

from piano_app.domain.score.models.graph import Edge, Node
from piano_app.domain.score.services.cleanup.delete_request import DeleteRequest
from piano_app.domain.score.services.cleanup.deletion_context import DeletionContext
from piano_app.domain.score.services.cleanup.registry import (
    CleanupRule,
    CleanupRuleRegistry,
)
from piano_app.domain.score.services.graph_service import GraphService


class CleanupEngine:
    def __init__(
        self,
        *,
        graph_service: GraphService,
        cleanup_rules: CleanupRuleRegistry,
    ) -> None:
        self._graph_service: GraphService = graph_service
        self._cleanup_rules: CleanupRuleRegistry = cleanup_rules

    def _delete_node_raw(self, node: Node) -> None:
        self._graph_service.remove_edges_of(node)
        self._graph_service.remove_node(node)

    def delete(self, initial_request: DeleteRequest) -> None:
        queue: deque[DeleteRequest] = deque([initial_request])

        deleted_nodes: set[Node] = set()

        while queue:
            request: DeleteRequest = queue.popleft()

            node_to_delete: Node = request.node

            if node_to_delete in deleted_nodes:
                continue

            outgoing_edges: list[Edge] = self._graph_service.outgoing_edges_of(
                node_to_delete
            )
            incoming_edges: list[Edge] = self._graph_service.incoming_edges_of(
                node_to_delete
            )

            self._delete_node_raw(node_to_delete)
            deleted_nodes.add(node_to_delete)

            context: DeletionContext = DeletionContext(
                node=node_to_delete,
                outgoing_edges=outgoing_edges,
                incoming_edges=incoming_edges,
            )

            rules: list[CleanupRule] = self._cleanup_rules.get_rules_for(node_to_delete)
            for rule in rules:
                queue.extend(rule(context))
