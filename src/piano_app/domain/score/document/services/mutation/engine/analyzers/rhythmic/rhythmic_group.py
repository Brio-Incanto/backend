from piano_app.domain.score.document.models.structural.rhythm import (
    GroupRhythmicContainer,
    LeafRhythmicContainer,
)
from piano_app.domain.score.document.services.mutation.engine.analyzers.base import MutationAnalyzer
from piano_app.domain.score.document.services.mutation.engine.buffer import EmitBuffer
from piano_app.domain.score.document.services.mutation.engine.resolver import ResolveBound
from piano_app.domain.score.document.services.mutation.instructions.actions.rhythmic import (
    DeleteRhythmicGroupAction,
)
from piano_app.domain.score.document.services.mutation.instructions.requests.rhythmic import (
    DeleteLeafRequest,
    DeleteRhythmicGroupRequest,
)


class DeleteRhythmicGroupAnalyzer(MutationAnalyzer[DeleteRhythmicGroupRequest]):
    """Decides the rhythmic group's deletion cascade.

    Every direct leaf and subgroup triggers its own deletion before the group.
    """

    def analyze(
        self,
        *,
        request: DeleteRhythmicGroupRequest,
        resolver: ResolveBound,
    ) -> EmitBuffer:
        buffer: EmitBuffer = EmitBuffer(request=request)
        group: GroupRhythmicContainer = request.target

        for child in group.children:
            if isinstance(child, LeafRhythmicContainer):
                buffer.incorporate(item=DeleteLeafRequest(target=child))
            elif isinstance(child, GroupRhythmicContainer):
                buffer.incorporate(item=DeleteRhythmicGroupRequest(target=child))
            else:
                raise ValueError(f"Unknown container type: {type(child)}")

        buffer.incorporate(item=DeleteRhythmicGroupAction(target=group))

        return buffer
