from collections import defaultdict
from collections.abc import Callable

from piano_app.domain.score.models.graph import Node

from .delete_request import DeleteRequest
from .deletion_context import DeletionContext

type CleanupRule = Callable[[DeletionContext], list[DeleteRequest]]


class CleanupRuleRegistry:
    def __init__(self) -> None:
        self._rules_by_node_type: dict[type[Node], list[CleanupRule]] = defaultdict(
            list
        )

    def register_rule[T: Node](
        self,
        *,
        node_type: type[T],
        rule: CleanupRule,
    ) -> None:
        self._rules_by_node_type[node_type].append(rule)

    def get_rules_for(self, node: Node) -> list[CleanupRule]:
        matching_rules: list[CleanupRule] = []

        for node_type, rules in self._rules_by_node_type.items():
            if isinstance(node, node_type):
                matching_rules.extend(rules)

        return matching_rules


# global singleton should be reconsidered
cleanup_rule_registry: CleanupRuleRegistry = CleanupRuleRegistry()


def cleanup_rule[T: Node](node_type: type[T]) -> Callable[[CleanupRule], CleanupRule]:
    def decorator(rule: CleanupRule) -> CleanupRule:
        cleanup_rule_registry.register_rule(node_type=node_type, rule=rule)
        return rule

    return decorator
