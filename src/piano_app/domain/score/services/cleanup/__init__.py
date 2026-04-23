from .default_rules import (
    remove_belonging_nodes_after_node_removal,
    remove_contained_nodes_after_node_removal,
    stitch_neighbors_after_node_removal,
)
from .delete_request import DeleteRequest
from .deletion_context import DeletionContext
from .engine import CleanupEngine
from .registry import (
    CleanupRule,
    CleanupRuleDecoratorFactory,
    CleanupRuleRegistry,
    RuleRegistration,
    create_cleanup_rule_decorator,
)

__all__ = (
    "CleanupEngine",
    "CleanupRule",
    "CleanupRuleDecoratorFactory",
    "CleanupRuleRegistry",
    "DeleteRequest",
    "DeletionContext",
    "RuleRegistration",
    "create_cleanup_rule_decorator",
    "remove_belonging_nodes_after_node_removal",
    "remove_contained_nodes_after_node_removal",
    "stitch_neighbors_after_node_removal",
)
