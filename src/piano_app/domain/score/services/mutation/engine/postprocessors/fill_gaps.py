from collections.abc import Sequence

from piano_app.domain.score.models.structural import Voice
from piano_app.domain.score.services.helpers import (
    Coverage,
    RhythmicSizeMapper,
    slice_measures,
)
from piano_app.domain.score.services.mutation.instructions import (
    MutationAction,
    MutationRequest,
)
from piano_app.domain.score.services.mutation.instructions.requests.system import FillRestRequest
from piano_app.domain.score.services.mutation.engine.projection import (
    VoiceCoverageDelta,
    collect_per_voice_coverage_deltas,
    project_voice,
)
from piano_app.domain.score.services.resolution import StaffResolver


class FillGapsPostprocessor:
    _FILLED_STAFF_STEP: int = 6

    def __init__(self):
        self._size_mapper: RhythmicSizeMapper = RhythmicSizeMapper()
        self._staff_resolver: StaffResolver = StaffResolver()

    # TODO fix and finish
    def search_fixes(
        self,
        *,
        planned_actions: list[MutationAction],
    ) -> Sequence[MutationRequest]:
        # create a map of affected voices and new diffs
        affected_voices: dict[Voice, VoiceCoverageDelta] = collect_per_voice_coverage_deltas(
            actions=planned_actions
        )

        fill_requests: list[FillRestRequest] = []

        # build a coverage tree over affected voice and affected rhythmic groups inside
        for voice, delta in affected_voices.items():
            voice_coverage: Coverage = project_voice(
                voice=voice,
                created=delta.created,
                deleted=delta.deleted,
            )

            #

            # dive into the coverage tree to detect all gaps
            for gap in voice_coverage.gaps_hierarchy:
                # TODO find a proper sourcer for measures or move full resolution to slicer
                for measure_slice in slice_measures(interval_to_slice=gap, origin_measure=None):
                    for mapped_size in self._size_mapper.spell_duration(
                        duration=measure_slice.length
                    ):
                        fill_requests.append(
                            FillRestRequest(
                                parent=gap.scope,
                                written_value=mapped_size,
                                staff=self._staff_resolver.resolve(
                                    voice=voice,
                                    measure=measure_slice.measure,
                                    position=None,
                                    deleted=None,
                                    actions=None,
                                ),
                                staff_step=self._FILLED_STAFF_STEP,
                                measure=measure_slice.measure,
                                position=None,
                            )
                        )

        return fill_requests
