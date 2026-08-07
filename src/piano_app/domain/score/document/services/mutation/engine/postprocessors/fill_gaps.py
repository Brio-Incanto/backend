from collections.abc import Sequence
from fractions import Fraction

from piano_app.domain.score.document.models import ScoreDocument
from piano_app.domain.score.document.models.material import Rest
from piano_app.domain.score.document.models.notation import DottedRhythmicValue
from piano_app.domain.score.document.models.structural import Measure, MeasurePosition
from piano_app.domain.score.document.services.helpers import (
    Coverage,
    Interval,
    RhythmicSizeMapper,
    measure_origin,
    translate_to_root,
)
from piano_app.domain.score.document.services.helpers.searching import find_measure_at_position
from piano_app.domain.score.document.services.mutation.instructions import (
    MutationRejectedError,
    ResultRef,
)
from piano_app.domain.score.document.services.mutation.instructions.requests.material import (
    CreateRestRequest,
)
from piano_app.domain.score.document.services.resolution import StaffPlacement, StaffResolver

from .base import MutatedStatePostprocessor


class FillGapsPostprocessor(MutatedStatePostprocessor):
    """Searches for gaps in each voice (gaps appear when a measure is not filled fully in voice),
    and creates a rest in each gap.
    """

    def __init__(self) -> None:
        self._size_mapper: RhythmicSizeMapper = RhythmicSizeMapper()
        self._staff_resolver: StaffResolver = StaffResolver()

    def search_fixes(
        self,
        *,
        document: ScoreDocument,
    ) -> Sequence[CreateRestRequest]:
        fill_requests: list[CreateRestRequest] = []

        for voice in document.voices:
            voice_coverage: Coverage = Coverage.build_coverage_hierarchy_from(
                owner=voice,
                origin_measure=document.measures[0],
            )

            for gap in voice_coverage.gaps_hierarchy:
                try:
                    mapped_sizes: list[DottedRhythmicValue] = self._size_mapper.spell_duration(
                        duration=gap.length
                    )
                except ValueError as error:
                    raise MutationRejectedError(
                        f"Cannot spell gap {gap.length} in "
                        f"{type(gap.scope).__name__} at {gap.start}."
                    ) from error

                offset: Fraction = Fraction(0)
                for mapped in mapped_sizes:
                    local_piece = Interval.of_span(
                        scope=gap.scope,
                        start=gap.start + offset,
                        length=mapped.fraction,
                    )
                    global_piece = translate_to_root(interval=local_piece)
                    measure: Measure = find_measure_at_position(
                        position=global_piece.start,
                        first_measure=document.measures[0],
                    )
                    position: MeasurePosition = MeasurePosition.of_fraction(
                        fraction=global_piece.start - measure_origin(measure=measure),
                    )
                    placement: StaffPlacement = self._staff_resolver.resolve(
                        voice=voice,
                        measure=measure,
                        position=position,
                    )
                    fill_requests.append(
                        CreateRestRequest(
                            voice=voice,
                            staff=placement.staff,
                            measure=measure,
                            position=position,
                            written_value=mapped,
                            staff_step=placement.staff_step,
                            out=ResultRef[Rest](),
                        )
                    )

                    offset += mapped.fraction

        return fill_requests
