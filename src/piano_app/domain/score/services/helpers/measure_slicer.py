from dataclasses import dataclass
from fractions import Fraction

from piano_app.domain.score.models.structural import Measure, MeasurePosition, Voice

from .interval import Interval
from .scope import (
    build_measure_interval_map,
    measure_origin,
    translate_to_root,
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


def slice_measures(
    *,
    interval: Interval,
    origin_measure: Measure,
) -> list[MeasureSlice]:
    root_interval: Interval = translate_to_root(interval=interval)
    # translate_to_root recurses up to the voice, so the root scope is always the voice
    root_scope = root_interval.scope
    if not isinstance(root_scope, Voice):
        raise ValueError("Root interval scope must be a voice.")
    voice: Voice = root_scope

    measure_interval_map: dict[Measure, Interval] = build_measure_interval_map(
        origin_measure=origin_measure,
        voice=voice,
    )

    slices: list[MeasureSlice] = []
    for measure, measure_interval in measure_interval_map.items():
        common_part: Interval | None = measure_interval.intersection(root_interval)
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
