from collections import defaultdict
from collections.abc import Callable

from piano_app.domain.score.models.graph import Node

from .delete_request import DeleteRequest
from .deletion_context import DeletionContext

type CleanupRule = Callable[[DeletionContext], list[DeleteRequest]]
type RuleDecorator = Callable[[CleanupRule], CleanupRule]
type CleanupRuleDecoratorFactory = Callable[[type[Node]], RuleDecorator]
type RuleRegistration = tuple[type[Node], CleanupRule]


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

    def get_rules_for(
        self,
        node: Node,
    ) -> list[CleanupRule]:
        matching_rules: list[CleanupRule] = []

        for node_type, rules in self._rules_by_node_type.items():
            if isinstance(node, node_type):
                matching_rules.extend(rules)

        return matching_rules


def create_cleanup_rule_decorator(
    storage: list[RuleRegistration],
) -> CleanupRuleDecoratorFactory:
    def cleanup_rule[T: Node](
        apply_to_type: type[T],
    ) -> RuleDecorator:
        def decorator(
            rule: CleanupRule,
        ) -> CleanupRule:
            storage.append((apply_to_type, rule))
            return rule

        return decorator

    return cleanup_rule
