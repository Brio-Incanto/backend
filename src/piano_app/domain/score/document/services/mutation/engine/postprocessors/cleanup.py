from collections.abc import Sequence

from piano_app.domain.score.document.models import ScoreDocument
from piano_app.domain.score.document.models.material import NoteCarrier, RestCarrier
from piano_app.domain.score.document.services.mutation.engine.postprocessors import (
    MutatedStatePostprocessor,
)
from piano_app.domain.score.document.services.mutation.instructions import MutationRequest
from piano_app.domain.score.document.services.mutation.instructions.requests.material import (
    DeleteNoteCarrierRequest,
    DeleteRestCarrierRequest,
)
from piano_app.domain.score.document.services.mutation.instructions.requests.rhythmic import (
    DeleteLeafRequest,
)
from piano_app.domain.score.document.services.mutation.instructions.requests.temporal import (
    DeleteTemporalAnchorRequest,
)


class CleanupPostprocessor(MutatedStatePostprocessor):
    """Removes childless scaffolding left by deletions — empty carriers, carrier-less
    leaves and orphan anchors. Never groups (an all-rest tuplet is valid, §6). One level
    per pass; the fixpoint unwinds carrier → leaf → anchor.
    """

    def search_fixes(
        self,
        *,
        document: ScoreDocument,
    ) -> Sequence[MutationRequest]:
        cleanup_requests: list[MutationRequest] = []

        for measure in document.measures:
            for anchor in measure.anchors:
                if anchor.is_orphan:
                    cleanup_requests.append(DeleteTemporalAnchorRequest(target=anchor))
                    continue

                for leaf in anchor.leaf_containers:
                    carrier = leaf.carrier
                    if carrier is None:
                        cleanup_requests.append(DeleteLeafRequest(target=leaf))
                        continue

                    if isinstance(carrier, NoteCarrier) and not carrier.notes:
                        cleanup_requests.append(DeleteNoteCarrierRequest(target=carrier))
                    elif isinstance(carrier, RestCarrier) and carrier.rest is None:
                        cleanup_requests.append(DeleteRestCarrierRequest(target=carrier))

        return cleanup_requests
