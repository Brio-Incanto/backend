from piano_app.domain.score.models.graph.nodes.material import Carrier, StaffElement
from piano_app.domain.score.models.graph.nodes.structural import (
    Measure,
    MeasureTimePoint,
    Staff,
    Voice,
)
from piano_app.domain.score.services.cleanup import (
    CleanupRuleDecoratorFactory,
    CleanupRuleRegistry,
    DeleteRequest,
    DeletionContext,
    RuleRegistration,
    create_cleanup_rule_decorator,
    remove_belonging_nodes_after_node_removal,
    remove_contained_nodes_after_node_removal,
    stitch_neighbors_after_node_removal,
)

_REGISTERED_RULES: list[RuleRegistration] = []
cleanup_rule: CleanupRuleDecoratorFactory = create_cleanup_rule_decorator(
    _REGISTERED_RULES
)


@cleanup_rule(Measure)
def remove_time_points_after_measure_removal(
    context: DeletionContext,
) -> list[DeleteRequest]:
    return remove_contained_nodes_after_node_removal(
        affected_type=MeasureTimePoint,
        context=context,
    )


@cleanup_rule(Voice)
def remove_carriers_after_voice_removal(
    context: DeletionContext,
) -> list[DeleteRequest]:
    return remove_belonging_nodes_after_node_removal(
        affected_type=Carrier,
        context=context,
    )


@cleanup_rule(Staff)
def remove_staff_elements_after_staff_removal(
    context: DeletionContext,
) -> list[DeleteRequest]:
    return remove_belonging_nodes_after_node_removal(
        affected_type=StaffElement,
        context=context,
    )


@cleanup_rule(Measure)
def stitch_measures_after_measure_removal(
    context: DeletionContext,
) -> list[DeleteRequest]:
    return stitch_neighbors_after_node_removal(
        affected_type=Measure,
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
