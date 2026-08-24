from collections.abc import Sequence
from fractions import Fraction

from piano_app.domain.score.document.models import ScoreDocument
from piano_app.domain.score.document.models.material import Rest
from piano_app.domain.score.document.models.notation import DottedRhythmicValue
from piano_app.domain.score.document.models.structural import Measure, MeasurePosition, Voice
from piano_app.domain.score.document.models.structural.rhythm import GroupRhythmicContainer
from piano_app.domain.score.document.services.geometry import Point, Span, gaps, interior
from piano_app.domain.score.document.services.geometry.score_geometry import ScoreGeometry
from piano_app.domain.score.document.services.helpers import RhythmicSizeMapper
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
    """Keeps every occupied region of every voice tiled, filling what is left with rests.

    Geometry reports holes without judging them; which holes deserve rests is decided
    here, and the two rules are deliberately NOT symmetric:

    * a measure a voice never reaches is **asleep** — it reports as one measure-long
      hole and is skipped, so an empty voice stays empty instead of sprouting rests;
    * a tuplet that exists has its interior occupied by definition, so it is **always**
      tiled in full and never sleeps.
    """

    def __init__(self) -> None:
        self._size_mapper: RhythmicSizeMapper = RhythmicSizeMapper()
        self._staff_resolver: StaffResolver = StaffResolver()

    def search_fixes(
        self,
        *,
        document: ScoreDocument,
    ) -> Sequence[CreateRestRequest]:
        if not document.measures:
            return []

        geometry: ScoreGeometry = ScoreGeometry(origin=document.measures[0])

        fill_requests: list[CreateRestRequest] = []
        for voice in document.voices:
            for gap in self._gaps_of_voice(geometry=geometry, voice=voice):
                fill_requests.extend(self._fill(geometry=geometry, voice=voice, gap=gap))

        return fill_requests

    def _gaps_of_voice(self, *, geometry: ScoreGeometry, voice: Voice) -> list[Span]:
        return [
            *self._measure_gaps(geometry=geometry, voice=voice),
            *self._nested_gaps(geometry=geometry, scope=voice),
        ]

    def _measure_gaps(self, *, geometry: ScoreGeometry, voice: Voice) -> list[Span]:
        """Holes in the measures this voice actually reaches into."""
        covered: list[Span] = [span for _, span in geometry.contents_of(scope=voice)]

        # THE SLEEPING RULE. A measure with no content of this voice is asleep, not
        # empty: it is not a bucket at all, so nothing fills it. Drop this filter and
        # every silent measure of every voice sprouts rests.
        awake: list[Span] = [
            region
            for _, region in geometry.measure_regions()
            if any(region.intersects(covered_span) for covered_span in covered)
        ]

        return [hole for bucket in awake for hole in gaps(bucket=bucket, covered=covered)]

    def _nested_gaps(
        self,
        *,
        geometry: ScoreGeometry,
        scope: Voice | GroupRhythmicContainer,
    ) -> list[Span]:
        found: list[Span] = []

        for child in scope.children:
            if not isinstance(child, GroupRhythmicContainer):
                continue

            covered: list[Span] = [span for _, span in geometry.contents_of(scope=child)]
            # no sleeping rule here, on purpose: the group's whole interior is one
            # bucket and it is always live while the group exists
            found.extend(
                gaps(
                    bucket=interior(frame=geometry.of_group(group=child)),
                    covered=covered,
                )
            )
            found.extend(self._nested_gaps(geometry=geometry, scope=child))

        return found

    def _fill(
        self,
        *,
        geometry: ScoreGeometry,
        voice: Voice,
        gap: Span,
    ) -> list[CreateRestRequest]:
        try:
            mapped_sizes: list[DottedRhythmicValue] = self._size_mapper.spell_duration(
                duration=gap.length
            )
        except ValueError as error:
            raise MutationRejectedError(f"Cannot spell gap {gap.length} at {gap.start}.") from error

        requests: list[CreateRestRequest] = []

        offset: Fraction = Fraction(0)
        for mapped in mapped_sizes:
            piece: Span = Span(
                frame=gap.frame,
                start=gap.start + offset,
                length=mapped.fraction,
            )
            at: Point = piece.start_point.to(frame=geometry.root)

            measure: Measure | None = geometry.measure_at(point=at)
            if measure is None:
                # the lookup reports the fact; refusing the gesture is this
                # postprocessor's own call
                raise MutationRejectedError(f"Gap at {at.value} lies past the last measure.")

            position: MeasurePosition = MeasurePosition.of_fraction(
                fraction=at.to(frame=geometry.of_measure(measure=measure)).value,
            )
            placement: StaffPlacement = self._staff_resolver.resolve(
                geometry=geometry,
                voice=voice,
                at=at,
            )

            requests.append(
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

        return requests
