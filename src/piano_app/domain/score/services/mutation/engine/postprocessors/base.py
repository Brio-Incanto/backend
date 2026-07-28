from abc import ABC, abstractmethod
from collections.abc import Sequence

from piano_app.domain.score.models import ScoreDocument
from piano_app.domain.score.services.mutation.instructions import MutationRequest


class MutatedStatePostprocessor(ABC):
    """Postprocessors are intended to guard a per gesture invariants
    which cannot be enforced by the analyzers
    and that should not be precalculated by the compilers.
    """

    @abstractmethod
    def search_fixes(
        self,
        *,
        document: ScoreDocument,
    ) -> Sequence[MutationRequest]: ...
