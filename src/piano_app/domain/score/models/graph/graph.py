from dataclasses import dataclass, field

from .edge import Edge
from .node import Node


@dataclass(slots=True, kw_only=True)
class Graph:
    nodes: list[Node] = field(default_factory=list)
    edges: list[Edge] = field(default_factory=list)
