from piano_app.domain.score.models.graph import EdgeRelation, Node
from piano_app.domain.score.services.cleanup import DeleteRequest, DeletionContext


def remove_contained_nodes_after_node_removal[T: Node](
    affected_type: type[T],
    context: DeletionContext,
) -> list[DeleteRequest]:
    nodes: list[T] = [
        edge.target
        for edge in context.outgoing_edges
        if edge.relation == EdgeRelation.CONTAINS
        and isinstance(edge.target, affected_type)
    ]

    return [DeleteRequest(node=node) for node in nodes]


def remove_belonging_nodes_after_node_removal[T: Node](
    affected_type: type[T],
    context: DeletionContext,
) -> list[DeleteRequest]:
    nodes: list[T] = [
        edge.source
        for edge in context.incoming_edges
        if edge.relation == EdgeRelation.BELONGS_TO
        and isinstance(edge.source, affected_type)
    ]

    return [DeleteRequest(node=node) for node in nodes]


def stitch_neighbors_after_node_removal[T: Node](
    affected_type: type[T],
    context: DeletionContext,
) -> list[DeleteRequest]:
    previous_nodes: list[T] = [
        edge.source
        for edge in context.incoming_edges
        if edge.relation == EdgeRelation.PRECEDES
        and isinstance(edge.source, affected_type)
    ]

    next_nodes: list[T] = [
        edge.target
        for edge in context.outgoing_edges
        if edge.relation == EdgeRelation.PRECEDES
        and isinstance(edge.target, affected_type)
    ]

    if previous_nodes and next_nodes:
        context.graph_service.connect(
            source=previous_nodes[0],
            target=next_nodes[0],
            relation=EdgeRelation.PRECEDES,
        )

    return []
