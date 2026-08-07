from piano_app.domain.score.document.models.material import CarrierOwner, Note
from piano_app.domain.score.document.models.relations import Tie
from piano_app.domain.score.document.models.structural import Voice
from piano_app.domain.score.document.models.structural.rhythm import LeafRhythmicContainer
from piano_app.domain.score.document.services.helpers import (
    Interval,
    interval_in_parent_scope,
    iter_leaves,
    translate_to_root,
    voice_of,
)
from piano_app.domain.score.document.services.mutation.engine.analyzers.base import MutationAnalyzer
from piano_app.domain.score.document.services.mutation.engine.buffer import EmitBuffer
from piano_app.domain.score.document.services.mutation.engine.resolver import ResolveBound
from piano_app.domain.score.document.services.mutation.instructions import MutationRejectedError
from piano_app.domain.score.document.services.mutation.instructions.actions.relations import (
    CreateTieAction,
)
from piano_app.domain.score.document.services.mutation.instructions.requests.relations import (
    CreateTieRequest,
)


class CreateTieAnalyzer(MutationAnalyzer[CreateTieRequest]):
    """Decides whether two metric notes may be connected by a tie.

    Their carriers must be consecutive and touching in one voice, with the
    corresponding outgoing and incoming tie ends available. Equal-pitch
    validation is deferred until note pitch is implemented.
    """

    def analyze(
        self,
        *,
        request: CreateTieRequest,
        resolver: ResolveBound,
    ) -> EmitBuffer:
        buffer: EmitBuffer = EmitBuffer(request=request)

        # TODO
        #  PITCH-VALIDATION (deferred — pitch is not in v1): a tie is only valid between
        #  two notes of the SAME pitch; reject otherwise once pitch is implemented.

        start_note: Note = resolver(request.start_note)
        end_note: Note = resolver(request.end_note)

        # other ties check
        if any(
            isinstance(relation, Tie) and relation.start is start_note
            for relation in start_note.relations
        ):
            raise MutationRejectedError("Note already starts another tie.")

        if any(
            isinstance(relation, Tie) and relation.end is end_note
            for relation in end_note.relations
        ):
            raise MutationRejectedError("Note already ends another tie.")

        # TODO add support for grace notes
        start_leaf: CarrierOwner = start_note.note_carrier.owner
        end_leaf: CarrierOwner = end_note.note_carrier.owner
        if not isinstance(start_leaf, LeafRhythmicContainer) or not isinstance(
            end_leaf,
            LeafRhythmicContainer,
        ):
            raise MutationRejectedError("Ties involving grace notes are not yet supported.")

        # same voice check
        start_voice: Voice = voice_of(start_leaf)
        end_voice: Voice = voice_of(end_leaf)
        if start_voice is not end_voice:
            raise MutationRejectedError("Ties are allowed only between notes in the same voice.")

        # neighbourhood check
        leaves: list[LeafRhythmicContainer] = iter_leaves(start_voice)
        start_index: int = leaves.index(start_leaf)
        if start_index + 1 == len(leaves) or leaves[start_index + 1] is not end_leaf:
            raise MutationRejectedError("Ties are allowed only between adjacent notes.")

        # prevent cases if there is a gap between the two notes
        start_interval: Interval = translate_to_root(
            interval=interval_in_parent_scope(container=start_leaf)
        )
        end_interval: Interval = translate_to_root(
            interval=interval_in_parent_scope(container=end_leaf)
        )
        if start_interval.end != end_interval.start:
            raise MutationRejectedError("Tied notes must touch on the voice timeline.")

        buffer.incorporate(
            item=CreateTieAction(
                start_note=start_note,
                end_note=end_note,
                out=request.out,
            ),
        )

        return buffer
