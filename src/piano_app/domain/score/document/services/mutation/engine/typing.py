from piano_app.domain.score.document.services.mutation.instructions import (
    MutationAction,
    MutationRequest,
)

"""What an analyzer emits: a further request to expand, or a terminal action."""
type MutationWorkItem = MutationRequest | MutationAction
