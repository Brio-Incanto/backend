from dataclasses import dataclass
from fractions import Fraction

from piano_app.domain.score.models.structural import Measure, MeasurePosition
from piano_app.domain.score.services.rhythmic_size.primitives.interval import Interval
from piano_app.domain.score.services.rhythmic_size.primitives.space import (
    measure_global_interval,
    measure_origin,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class MeasureSlice:
    measure: Measure
    global_start_position: Fraction
    global_end_position: Fraction

    # derive a fraction here and not a rhythmic value,
    # because size mapping is not a responsibility of the slicer
    @property
    def length(self) -> Fraction:
        return self.global_end_position - self.global_start_position

    @property
    def start_measure_position(self) -> MeasurePosition:
        global_measure_start: Fraction = measure_origin(measure=self.measure)

        return MeasurePosition.of_fraction(
            fraction=self.global_start_position - global_measure_start
        )

    @property
    def end_measure_position(self) -> MeasurePosition:
        global_measure_start: Fraction = measure_origin(measure=self.measure)

        return MeasurePosition.of_fraction(fraction=self.global_end_position - global_measure_start)


class MeasureSlicer:
    def slice(
        self,
        *,
        interval: Interval,
        origin_measure: Measure,
    ) -> list[MeasureSlice]:
        measure_interval_map: dict[Measure, GlobalInterval] = self._build_measure_interval_map(
            origin_measure=origin_measure
        )

        slices: list[MeasureSlice] = []
        for measure, measure_interval in measure_interval_map.items():
            common_part: Interval | None = measure_interval.interval.intersection(
                interval_to_slice.interval
            )
            if common_part is None:
                continue

            slices.append(
                MeasureSlice(
                    measure=measure,
                    global_start_position=common_part.start,
                    global_end_position=common_part.end,
                )
            )

        return slices

    # inefficient due to n + 1
    # global interval for each measure is calculated
    # by finding the cumulative sum of all preceding without caching
    def _build_measure_interval_map(
        self,
        *,
        origin_measure: Measure,
    ) -> dict[Measure, GlobalInterval]:
        measure_interval_map: dict[Measure, GlobalInterval] = {}

        # add all preceding measures to the map
        previous: Measure | None = origin_measure.prev_measure
        while previous is not None:
            measure_interval_map[previous] = measure_global_interval(measure=previous)
            previous = previous.prev_measure

        # add the origin measure to the map
        measure_interval_map[origin_measure] = measure_global_interval(measure=origin_measure)

        # add all following measures to the map
        following: Measure | None = origin_measure.next_measure
        while following is not None:
            measure_interval_map[following] = measure_global_interval(measure=following)
            following = following.next_measure

        return measure_interval_map
