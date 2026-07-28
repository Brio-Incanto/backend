from fractions import Fraction

from piano_app.domain.score.models.notation import (
    DottedRhythmicValue,
    RhythmicValue,
)


class RhythmicSizeMapper:
    """Normalises an arbitrary duration into notatable rhythmic sizes."""

    # Max dots allowed on a single normalized size
    _MAX_SINGLE_SIZE_DOTS_COUNT: int = 2
    # Max dots allowed on a multi-size decomposition
    _MAX_MULTI_SIZE_DOTS_COUNT: int = 1
    # How much smaller (by denominator) a value may be than the largest selected
    _MAX_DENOMINATOR_JUMP: int = 4
    # The shortest note in the model, dotting cannot reach below it
    _SMALLEST_NOTE: int = max(RhythmicValue)

    def spell_duration(self, *, duration: Fraction) -> list[DottedRhythmicValue]:
        """Return the rhythmic sizes that spell duration

        Prefers a single dotted value; falls back to a multi-size decomposition.
        Raises ``ValueError`` if the duration cannot be normalized under the
        constraints.
        """
        if duration <= 0:
            raise ValueError("Duration must be positive.")

        single_size: DottedRhythmicValue | None = self._find_single_size(
            target_duration=duration,
        )

        if single_size is not None:
            return [single_size]

        result: list[DottedRhythmicValue] = self._find_multi_size_decomposition(
            target_duration=duration,
        )

        if not result:
            raise ValueError(f"Cannot normalize rhythmic duration: {duration}.")

        return result

    def _find_single_size(
        self,
        *,
        target_duration: Fraction,
    ) -> DottedRhythmicValue | None:
        """The one dotted value whose duration equals the target, or ``None``."""
        for candidate in self._build_single_size_candidates():
            if candidate.fraction == target_duration:
                return candidate

        return None

    def _find_multi_size_decomposition(
        self,
        *,
        target_duration: Fraction,
    ) -> list[DottedRhythmicValue]:
        """Decompose the target into several sizes, or an empty list if impossible
        (the target is always positive, so a real decomposition is never empty)."""
        candidates: list[DottedRhythmicValue] = self._build_multi_size_candidates()

        return self._search_decomposition(
            remaining_duration=target_duration,
            candidates=candidates,
            selected_sizes=[],
        )

    def _search_decomposition(
        self,
        *,
        remaining_duration: Fraction,
        candidates: list[DottedRhythmicValue],
        selected_sizes: list[DottedRhythmicValue],
    ) -> list[DottedRhythmicValue]:
        """Backtracking search: pick sizes (value + count) largest-first until the
        remaining duration is exactly zero. Returns the selected sizes, or an empty
        list if this branch cannot be completed under the constraints (the search
        is only entered with a positive duration, so success is never empty)."""
        if remaining_duration == 0:
            return selected_sizes

        # Recurse only into candidates *after* the current one: order does not
        # matter, so building selections in one descending order avoids exploring
        # the same multiset as permutations. It also keeps the first selected size
        # the largest, which is the anchor for the denominator-jump constraint.
        largest_selected_value: RhythmicValue | None = (
            selected_sizes[0].value if selected_sizes else None
        )

        for index, candidate in enumerate(candidates):
            if candidate.fraction > remaining_duration:
                continue

            if not self._is_allowed_denominator_jump(
                candidate=candidate,
                largest_selected_value=largest_selected_value,
            ):
                continue

            max_count: int = remaining_duration // candidate.fraction

            for count in range(max_count, 0, -1):
                used_duration: Fraction = candidate.fraction * count
                next_remaining_duration: Fraction = remaining_duration - used_duration

                result = self._search_decomposition(
                    remaining_duration=next_remaining_duration,
                    candidates=candidates[index + 1 :],
                    selected_sizes=[
                        *selected_sizes,
                        *[candidate] * count,
                    ],
                )

                if result:
                    return result

        return []

    def _build_single_size_candidates(self) -> list[DottedRhythmicValue]:
        return self._build_candidates(max_dots=self._MAX_SINGLE_SIZE_DOTS_COUNT)

    def _build_multi_size_candidates(self) -> list[DottedRhythmicValue]:
        return self._build_candidates(max_dots=self._MAX_MULTI_SIZE_DOTS_COUNT)

    def _build_candidates(self, *, max_dots: int) -> list[DottedRhythmicValue]:
        """Every representable dotted value up to ``max_dots`` dots, sorted by
        duration descending (so the search tries the largest first)."""
        candidates: list[DottedRhythmicValue] = []

        for rhythmic_value in RhythmicValue:
            for dots_count in range(max_dots + 1):
                # Skip combinations the model forbids — dots that reach below the
                # smallest note (DottedRhythmicValue would reject them). Avoid
                # constructing them at all rather than catching the error.
                dotted_reach: int = rhythmic_value * 2**dots_count
                if dotted_reach > self._SMALLEST_NOTE:
                    continue

                candidates.append(
                    DottedRhythmicValue(
                        value=rhythmic_value,
                        dots_count=dots_count,
                    )
                )

        return sorted(
            candidates,
            key=lambda candidate: candidate.fraction,
            reverse=True,
        )

    def _is_allowed_denominator_jump(
        self,
        *,
        candidate: DottedRhythmicValue,
        largest_selected_value: RhythmicValue | None,
    ) -> bool:
        """Whether ``candidate`` is close enough to the largest already-selected
        value — keeps a decomposition from mixing far-apart values. Always allowed
        when nothing is selected yet (``largest_selected_value`` is ``None``)."""
        if largest_selected_value is None:
            return True

        max_allowed_denominator: int = largest_selected_value * self._MAX_DENOMINATOR_JUMP

        return candidate.value <= max_allowed_denominator
