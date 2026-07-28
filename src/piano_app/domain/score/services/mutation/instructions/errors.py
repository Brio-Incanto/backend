class PlanRejectedError(Exception):
    """Raised by an analyzer when the requested operation is impossible.

    The planner lets it propagate; the whole plan is discarded before any
    mutation happens, so no rollback is required. This is the explicit
    "reject" channel — an empty result from an analyzer means a legitimate
    no-op, not a rejection.
    """

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason
