from collections import defaultdict
from dataclasses import dataclass, field

from .edge import Edge
from .node import Node


@dataclass(slots=True, kw_only=True)
class Graph:
    _nodes: set[Node] = field(default_factory=set)
    _edges: set[Edge] = field(default_factory=set)

    _node_outgoing_edges: dict[Node, set[Edge]] = field(
        default_factory=lambda: defaultdict(set)
    )
    _node_incoming_edges: dict[Node, set[Edge]] = field(
        default_factory=lambda: defaultdict(set)
    )

    _next_node_id: int = 1

    def generate_node_id(self) -> int:
        node_id: int = self._next_node_id
        self._next_node_id += 1
        return node_id

    def nodes(self) -> frozenset[Node]:
        return frozenset(self._nodes)

    def edges(self) -> frozenset[Edge]:
        return frozenset(self._edges)

    def outgoing_edges(self, node: Node) -> frozenset[Edge]:
        if node not in self._nodes:
            raise ValueError(f"Node {node} not found in graph")

        return frozenset(self._node_outgoing_edges[node])

    def incoming_edges(self, node: Node) -> frozenset[Edge]:
        if node not in self._nodes:
            raise ValueError(f"Node {node} not found in graph")

        return frozenset(self._node_incoming_edges[node])

    def add_node(self, node: Node) -> Node:
        self._nodes.add(node)
        return node

    def add_edge(self, edge: Edge) -> Edge:
        self._edges.add(edge)
        self._node_outgoing_edges[edge.source].add(edge)
        self._node_incoming_edges[edge.target].add(edge)
        return edge

    def remove_node(self, node: Node) -> None:
        self._nodes.discard(node)
        self._node_outgoing_edges.pop(node, None)
        self._node_incoming_edges.pop(node, None)

    def remove_edge(self, edge: Edge) -> None:
        self._edges.discard(edge)
        self._node_outgoing_edges[edge.source].discard(edge)
        self._node_incoming_edges[edge.target].discard(edge)
