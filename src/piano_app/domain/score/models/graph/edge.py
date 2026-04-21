from dataclasses import dataclass

from .edge_relation import EdgeRelation
from .node import Node


@dataclass(
    frozen=True,
    slots=True,
    kw_only=True,
)
class Edge:
    source: Node
    target: Node
    relation: EdgeRelation
