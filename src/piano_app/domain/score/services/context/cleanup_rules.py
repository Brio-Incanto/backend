from piano_app.domain.score.services.cleanup import RuleRegistration
from piano_app.domain.score.services.cleanup.registry import (
    CleanupRuleDecoratorFactory,
    CleanupRuleRegistry,
    create_cleanup_rule_decorator,
)

_REGISTERED_RULES: list[RuleRegistration] = []
cleanup_rule: CleanupRuleDecoratorFactory = create_cleanup_rule_decorator(
    _REGISTERED_RULES
)


def register_cleanup_rules(
    cleanup_registry: CleanupRuleRegistry,
) -> None:
    for node_type, rule in _REGISTERED_RULES:
        cleanup_registry.register_rule(
            node_type=node_type,
            rule=rule,
        )
