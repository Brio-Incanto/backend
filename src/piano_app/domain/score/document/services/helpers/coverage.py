from dataclasses import dataclass
from fractions import Fraction

from piano_app.domain.score.document.models.structural import Measure, Voice
from piano_app.domain.score.document.models.structural.rhythm import GroupRhythmicContainer
from piano_app.domain.score.document.models.structural.rhythm.metric.parent import (
    RhythmicContainerParent,
)

from .interval import Interval
from .scope import build_measure_interval_map, interval_in_parent_scope


@dataclass(slots=True, kw_only=True, eq=False)
class Coverage:
    """A rhythmic space projected as buckets — uniform for a voice and a group.

    A space holds one or more **buckets** (bounded regions the tiling rule
    applies to: a non-empty bucket must be fully covered, an empty one sleeps).
    A voice is many buckets (its measures, on the global timeline) — some may be
    empty. A group is exactly one bucket (its whole interior, in local
    coordinates) — and, while it exists, that bucket is full. ``covered`` are the
    children's footprints in the space's own coordinates; ``children`` are the
    nested group spaces to descend into.
    """

    owner: RhythmicContainerParent
    covered: list[Interval]
    buckets: list[Interval]
    children: list[Coverage]

    @property
    def gaps(self) -> list[Interval]:
        return [gap for bucket in self.buckets for gap in bucket.subtract_many(self.covered)]

    @property
    def gaps_hierarchy(self) -> list[Interval]:
        return self.gaps + [gap for child in self.children for gap in child.gaps_hierarchy]

    @classmethod
    def build_coverage_hierarchy_from(
        cls,
        *,
        owner: RhythmicContainerParent,
        origin_measure: Measure,
    ) -> Coverage:
        if isinstance(owner, Voice):
            return cls._create_from_voice(
                owner=owner,
                children=[
                    Coverage.build_coverage_hierarchy_from(
                        owner=child,
                        origin_measure=origin_measure,
                    )
                    for child in owner.children
                    if isinstance(child, GroupRhythmicContainer)
                ],
                origin_measure=origin_measure,
            )

        if isinstance(owner, GroupRhythmicContainer):
            return cls._create_from_group(
                owner=owner,
                children=[
                    Coverage.build_coverage_hierarchy_from(
                        owner=child,
                        origin_measure=origin_measure,
                    )
                    for child in owner.children
                    if isinstance(child, GroupRhythmicContainer)
                ],
            )

        raise TypeError(f"Unsupported parent type: {type(owner).__name__}.")

    @classmethod
    def _create_from_voice(
        cls,
        *,
        owner: Voice,
        children: list[Coverage],
        origin_measure: Measure,
    ) -> Coverage:
        covered: list[Interval] = [
            interval_in_parent_scope(container=rhythmic_container)
            for rhythmic_container in owner.children
        ]

        measure_map: dict[Measure, Interval] = build_measure_interval_map(
            origin_measure=origin_measure,
            voice=owner,
        )
        buckets: list[Interval] = [
            measure_interval
            for measure_interval in measure_map.values()
            if any(measure_interval.intersects(cover_interval) for cover_interval in covered)
        ]

        return cls._create(owner=owner, covered=covered, buckets=buckets, children=children)

    @classmethod
    def _create_from_group(
        cls,
        *,
        owner: GroupRhythmicContainer,
        children: list[Coverage],
    ) -> Coverage:
        covered: list[Interval] = [
            interval_in_parent_scope(container=rhythmic_container)
            for rhythmic_container in owner.children
        ]

        buckets: list[Interval] = [
            Interval.of_span(scope=owner, start=Fraction(0), length=owner.written_size.fraction)
        ]

        return cls._create(owner=owner, covered=covered, buckets=buckets, children=children)

    @classmethod
    def _create(
        cls,
        *,
        owner: RhythmicContainerParent,
        covered: list[Interval],
        buckets: list[Interval],
        children: list[Coverage],
    ) -> Coverage:
        for interval in covered:
            if interval.scope is not owner:
                raise ValueError("Covered intervals must belong to the owner.")

        for bucket in buckets:
            if bucket.scope is not owner:
                raise ValueError("Buckets must belong to the owner.")

        for child in children:
            if not isinstance(child.owner, GroupRhythmicContainer):
                raise ValueError("Children must be groups.")

            if child.owner.parent is not owner:
                raise ValueError("Children must belong to the owner.")

        return cls(owner=owner, covered=covered, buckets=buckets, children=children)
