from piano_app.domain.score.models.graph import Edge, EdgeRelation
from piano_app.domain.score.models.graph.nodes.material import (
    Note,
    Rest,
    RestCarrier,
    SoundCarrier,
)
from piano_app.domain.score.services.cleanup.delete_request import DeleteRequest
from piano_app.domain.score.services.cleanup.deletion_context import DeletionContext
from piano_app.domain.score.services.cleanup.registry import cleanup_rule


def _owner_sound_carrier_from_deleted_note(
    incoming_edges: list[Edge],
) -> SoundCarrier | None:
    for edge in incoming_edges:
        if edge.relation == EdgeRelation.CONTAINS and isinstance(
            edge.source, SoundCarrier
        ):
            return edge.source

    return None


def _owner_rest_carrier_from_deleted_rest(
    incoming_edges: list[Edge],
) -> RestCarrier | None:
    for edge in incoming_edges:
        if edge.relation == EdgeRelation.CONTAINS and isinstance(
            edge.source, RestCarrier
        ):
            return edge.source

    return None


def _remaining_notes_of_sound_carrier(
    context: DeletionContext,
    carrier: SoundCarrier,
) -> list[Note]:
    return context.graph_service.target_nodes_of_type(
        carrier,
        node_type=Note,
        relation=EdgeRelation.CONTAINS,
    )


def _contained_rests_of_rest_carrier(
    context: DeletionContext,
    carrier: RestCarrier,
) -> list[Rest]:
    return context.graph_service.target_nodes_of_type(
        carrier,
        node_type=Rest,
        relation=EdgeRelation.CONTAINS,
    )


@cleanup_rule(Note)
def remove_empty_sound_carrier_after_note_removal(
    context: DeletionContext,
) -> list[DeleteRequest]:
    carrier: SoundCarrier | None = _owner_sound_carrier_from_deleted_note(
        context.incoming_edges,
    )
    if carrier is None:
        return []

    remaining_notes: list[Note] = _remaining_notes_of_sound_carrier(context, carrier)
    if remaining_notes:
        return []

    return [DeleteRequest(node=carrier)]


@cleanup_rule(Rest)
def remove_rest_carrier_after_rest_removal(
    context: DeletionContext,
) -> list[DeleteRequest]:
    carrier: RestCarrier | None = _owner_rest_carrier_from_deleted_rest(
        context.incoming_edges,
    )
    if carrier is None:
        return []

    return [DeleteRequest(node=carrier)]


@cleanup_rule(SoundCarrier)
def remove_notes_of_deleted_sound_carrier(
    context: DeletionContext,
) -> list[DeleteRequest]:
    notes: list[Note] = [
        edge.target
        for edge in context.outgoing_edges
        if edge.relation == EdgeRelation.CONTAINS and isinstance(edge.target, Note)
    ]

    return [DeleteRequest(node=note) for note in notes]


@cleanup_rule(RestCarrier)
def remove_rest_of_deleted_rest_carrier(
    context: DeletionContext,
) -> list[DeleteRequest]:
    rests: list[Rest] = [
        edge.target
        for edge in context.outgoing_edges
        if edge.relation == EdgeRelation.CONTAINS and isinstance(edge.target, Rest)
    ]

    return [DeleteRequest(node=rest) for rest in rests]
