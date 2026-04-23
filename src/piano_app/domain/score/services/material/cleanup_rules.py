from piano_app.domain.score.models.graph import EdgeRelation
from piano_app.domain.score.models.graph.nodes.material import (
    Note,
    Rest,
    RestCarrier,
    SoundCarrier,
)
from piano_app.domain.score.services.cleanup import (
    CleanupRuleDecoratorFactory,
    CleanupRuleRegistry,
    DeleteRequest,
    DeletionContext,
    RuleRegistration,
    create_cleanup_rule_decorator,
    remove_contained_nodes_after_node_removal,
)

_REGISTERED_RULES: list[RuleRegistration] = []
cleanup_rule: CleanupRuleDecoratorFactory = create_cleanup_rule_decorator(
    _REGISTERED_RULES
)


@cleanup_rule(Note)
def remove_empty_sound_carrier_after_note_removal(
    context: DeletionContext,
) -> list[DeleteRequest]:
    carriers: list[SoundCarrier] = [
        edge.source
        for edge in context.incoming_edges
        if edge.relation == EdgeRelation.CONTAINS
        and isinstance(edge.source, SoundCarrier)
    ]

    if not carriers:
        return []

    carrier: SoundCarrier = carriers[0]

    remaining_notes: list[Note] = context.graph_service.target_nodes_of_type(
        node=carrier,
        node_type=Note,
        relation=EdgeRelation.CONTAINS,
    )
    if remaining_notes:
        return []

    return [DeleteRequest(node=carrier)]


@cleanup_rule(Rest)
def remove_rest_carrier_after_rest_removal(
    context: DeletionContext,
) -> list[DeleteRequest]:
    carriers: list[RestCarrier] = [
        edge.source
        for edge in context.incoming_edges
        if edge.relation == EdgeRelation.CONTAINS
        and isinstance(edge.source, RestCarrier)
    ]

    if not carriers:
        return []

    return [DeleteRequest(node=carriers[0])]


@cleanup_rule(SoundCarrier)
def remove_notes_of_deleted_sound_carrier(
    context: DeletionContext,
) -> list[DeleteRequest]:
    return remove_contained_nodes_after_node_removal(
        affected_type=Note,
        context=context,
    )


@cleanup_rule(RestCarrier)
def remove_rest_of_deleted_rest_carrier(
    context: DeletionContext,
) -> list[DeleteRequest]:
    return remove_contained_nodes_after_node_removal(
        affected_type=Rest,
        context=context,
    )


def register_cleanup_rules(
    cleanup_registry: CleanupRuleRegistry,
) -> None:
    for node_type, rule in _REGISTERED_RULES:
        cleanup_registry.register_rule(
            node_type=node_type,
            rule=rule,
        )
