from collections import defaultdict
from dataclasses import dataclass
from fractions import Fraction

from piano_app.domain.score.models.material import NoteCarrier, RestCarrier
from piano_app.domain.score.models.material.primitive import MusicalItem
from piano_app.domain.score.models.structural import Measure, MeasurePosition, Staff, Voice
from piano_app.domain.score.models.structural.rhythm import LeafRhythmicContainer
from piano_app.domain.score.services.helpers import (
    Interval,
    flatten,
    global_position,
    interval_in_parent_scope,
    translate_to_root,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class StaffPlacement:
    """Where a system-produced element lands: a staff and a vertical step on it."""

    staff: Staff
    staff_step: int


@dataclass(frozen=True, slots=True, kw_only=True)
class _Observation:
    """A nearby element's placement, weighted by its proximity to the gap."""

    staff: Staff
    step: Fraction  # the element's (chord's) centre step on the staff
    weight: Fraction


# TODO possibly refactor
class StaffResolver:
    """Picks an approximated staff and step for a system-produced element (e.g. a fill rest)."""

    # how many nearest leaves to observe around the gap
    _WINDOW: int = 4

    # TODO collision shift on the resolved staff
    def resolve(
        self,
        *,
        voice: Voice,
        measure: Measure,
        position: MeasurePosition,
    ) -> StaffPlacement:
        target: Fraction = global_position(measure=measure, position=position)

        observations: list[_Observation] = self._observe(voice=voice, target=target)
        if not observations:
            raise ValueError("Cannot resolve a staff for an empty voice.")

        staff: Staff = self._dominant_staff(observations=observations)
        step: Fraction = self._mean_step(observations=observations, staff=staff)

        return StaffPlacement(staff=staff, staff_step=round(step))

    @staticmethod
    def _dominant_staff(*, observations: list[_Observation]) -> Staff:
        weight_by_staff: dict[Staff, Fraction] = defaultdict(Fraction)
        for observation in observations:
            weight_by_staff[observation.staff] += observation.weight

        return max(weight_by_staff, key=lambda staff: weight_by_staff[staff])

    @staticmethod
    def _mean_step(*, observations: list[_Observation], staff: Staff) -> Fraction:
        total_weight: Fraction = Fraction(0)
        weighted: Fraction = Fraction(0)
        for observation in observations:
            if observation.staff is staff:
                total_weight += observation.weight
                weighted += observation.weight * observation.step

        return weighted / total_weight

    def _observe(self, *, voice: Voice, target: Fraction) -> list[_Observation]:
        nearest: list[LeafRhythmicContainer] = sorted(
            flatten(voice),
            key=lambda container: self._distance_to_gap(leaf=container, target=target),
        )[: self._WINDOW]

        observations: list[_Observation] = []
        for leaf in nearest:
            distance: Fraction = self._distance_to_gap(leaf=leaf, target=target)
            proximity: Fraction = Fraction(1) / (1 + distance)
            observations.extend(self._observe_leaf(leaf=leaf, proximity=proximity))

        return observations

    # TODO intra-chord centre could use a non-uniform coefficient (outer/top notes)
    def _observe_leaf(
        self, *, leaf: LeafRhythmicContainer, proximity: Fraction
    ) -> list[_Observation]:
        steps_by_staff: dict[Staff, list[int]] = defaultdict(list)
        for item in self._items_of(leaf):
            steps_by_staff[item.staff].append(item.staff_step)

        note_count: int = sum(len(steps) for steps in steps_by_staff.values())
        observations: list[_Observation] = []
        for staff, steps in steps_by_staff.items():
            centre: Fraction = Fraction(sum(steps), len(steps))
            share: Fraction = Fraction(len(steps), note_count)
            observations.append(_Observation(staff=staff, step=centre, weight=proximity * share))

        return observations

    @staticmethod
    def _distance_to_gap(*, leaf: LeafRhythmicContainer, target: Fraction) -> Fraction:
        # measure against the leaf's whole global span, not just its start, so a long note
        # ending right at the gap counts as adjacent (distance 0) instead of being penalised
        span: Interval = translate_to_root(to_translate=interval_in_parent_scope(container=leaf))
        if span.start <= target <= span.end:
            return Fraction(0)
        if target < span.start:
            return span.start - target

        return target - span.end

    @staticmethod
    def _items_of(leaf: LeafRhythmicContainer) -> list[MusicalItem]:
        carrier = leaf.carrier
        if carrier is None:
            return []

        if isinstance(carrier, NoteCarrier):
            return list(carrier.notes)

        if isinstance(carrier, RestCarrier):
            rest = carrier.rest
            return [rest] if rest is not None else []

        raise TypeError(f"Unsupported carrier type: {type(carrier).__name__}.")
