from dataclasses import replace

from piano_app.domain.score.models.graph import Edge, EdgeRelation, Graph, Node


class GraphService:
    def __init__(self, graph: Graph) -> None:
        self._graph: Graph = graph

    def _register_node(self, node: Node) -> Node:
        return self._graph.add_node(node=node)

    def create_node[T: Node](
        self,
        node_type: type[T],
        **kwargs: object,
    ) -> T:
        node_id: int = self._graph.generate_node_id()
        node: T = node_type(id=node_id, **kwargs)
        self._register_node(node=node)
        return node

    def connect(
        self,
        *,
        source: Node,
        target: Node,
        relation: EdgeRelation,
    ) -> Edge:
        nodes: frozenset[Node] = self._graph.nodes()

        if source not in nodes:
            raise ValueError(f"Source node {source} not found in graph")

        if target not in nodes:
            raise ValueError(f"Target node {target} not found in graph")

        edge: Edge = Edge(
            source=source,
            target=target,
            relation=relation,
        )
        self._graph.add_edge(edge=edge)
        return edge

    def update_node[T: Node](
        self,
        old_node: T,
        **changes: object,
    ) -> T:
        if old_node not in self._graph.nodes():
            raise ValueError(f"Node {old_node} not found in graph")

        if "id" in changes:
            raise ValueError("Cannot change node id")

        new_node: T = replace(old_node, **changes)  # type: ignore[arg-type]

        old_incoming_edges: frozenset[Edge] = self._graph.incoming_edges(node=old_node)
        old_outgoing_edges: frozenset[Edge] = self._graph.outgoing_edges(node=old_node)

        self.remove_edges_of(node=old_node)
        self.remove_node(node=old_node)

        self._register_node(node=new_node)

        for edge in old_incoming_edges:
            self.connect(
                source=edge.source,
                target=new_node,
                relation=edge.relation,
            )

        for edge in old_outgoing_edges:
            self.connect(
                source=new_node,
                target=edge.target,
                relation=edge.relation,
            )

        return new_node

    def remove_node(self, node: Node) -> None:
        self._graph.remove_node(node=node)

    def remove_edge(self, edge: Edge) -> None:
        self._graph.remove_edge(edge=edge)

    def remove_edges_of(self, node: Node) -> None:
        outgoing_edges: frozenset[Edge] = self._graph.outgoing_edges(node=node)
        incoming_edges: frozenset[Edge] = self._graph.incoming_edges(node=node)
        connected_edges: frozenset[Edge] = outgoing_edges | incoming_edges

        for edge in connected_edges:
            self.remove_edge(edge=edge)

    def outgoing_edges_of(
        self,
        node: Node,
        relation: EdgeRelation | None = None,
    ) -> list[Edge]:
        all_outgoing: frozenset[Edge] = self._graph.outgoing_edges(node=node)

        return [
            edge
            for edge in all_outgoing
            if relation is None or edge.relation == relation
        ]

    def incoming_edges_of(
        self,
        *,
        node: Node,
        relation: EdgeRelation | None = None,
    ) -> list[Edge]:
        all_incoming: frozenset[Edge] = self._graph.incoming_edges(node=node)

        return [
            edge
            for edge in all_incoming
            if relation is None or edge.relation == relation
        ]

    def target_nodes_of(
        self,
        *,
        node: Node,
        relation: EdgeRelation | None = None,
    ) -> list[Node]:
        outgoing_edges: list[Edge] = self.outgoing_edges_of(
            node=node,
            relation=relation,
        )
        return [edge.target for edge in outgoing_edges]

    def source_nodes_of(
        self,
        *,
        node: Node,
        relation: EdgeRelation | None = None,
    ) -> list[Node]:
        incoming_edges: list[Edge] = self.incoming_edges_of(
            node=node,
            relation=relation,
        )
        return [edge.source for edge in incoming_edges]

    def target_nodes_of_type[T: Node](
        self,
        *,
        node: Node,
        node_type: type[T],
        relation: EdgeRelation | None = None,
    ) -> list[T]:
        return [
            related_node
            for related_node in self.target_nodes_of(node=node, relation=relation)
            if isinstance(related_node, node_type)
        ]

    def source_nodes_of_type[T: Node](
        self,
        *,
        node: Node,
        node_type: type[T],
        relation: EdgeRelation | None = None,
    ) -> list[T]:
        return [
            related_node
            for related_node in self.source_nodes_of(node=node, relation=relation)
            if isinstance(related_node, node_type)
        ]
