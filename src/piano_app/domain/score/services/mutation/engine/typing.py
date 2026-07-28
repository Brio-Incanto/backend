from piano_app.domain.score.services.mutation.instructions import (
    MutationAction,
    MutationRequest,
)

"""What an analyzer emits: a further request to expand, or a terminal action."""
type PlanItem = MutationRequest | MutationAction
