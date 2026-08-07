from collections.abc import Sequence
from dataclasses import dataclass

from piano_app.domain.score.document.models.structural import Measure, Staff, Voice

from .mutation_sink import DIRECT_SINK, MutationSink


@dataclass(slots=True, kw_only=True, eq=False)
class ScoreDocument:
    # voices / staffs are owned collections with no wiring method (fixed at
    # construction) → plain fields. measures is the linked chain the document
    # mutates through append/insert/remove → private + read-only view.
    _voices: list[Voice]
    _staffs: list[Staff]
    _measures: list[Measure]

    @property
    def voices(self) -> Sequence[Voice]:
        return self._voices

    @property
    def staffs(self) -> Sequence[Staff]:
        return self._staffs

    @property
    def measures(self) -> Sequence[Measure]:
        return self._measures

    @classmethod
    def create(
        cls,
        *,
        voices: list[Voice],
        staffs: list[Staff],
        measures: list[Measure],
    ) -> ScoreDocument:
        document: ScoreDocument = cls(_voices=voices, _staffs=staffs, _measures=[])
        for measure in measures:
            document.append_measure(measure=measure)

        return document

    def insert_measure_after(
        self,
        *,
        measure: Measure,
        after: Measure,
        sink: MutationSink = DIRECT_SINK,
    ) -> None:
        # guard from working with a measure that is not in the document
        if after not in self._measures:
            raise ValueError("Measure to insert after is not in the document.")

        # idempotency
        if measure in self._measures:
            return

        # not in this document, but already in a chain, disallow
        if measure.next_measure is not None or measure.prev_measure is not None:
            raise ValueError("Measure is already in a chain.")

        self._link_between(measure=measure, prev=after, nxt=after.next_measure, sink=sink)

        # safe because after is in the document at that point
        index: int = self._measures.index(after)
        sink.list_insert(self._measures, index + 1, measure)

    def append_measure(
        self,
        *,
        measure: Measure,
        sink: MutationSink = DIRECT_SINK,
    ) -> None:
        # idempotency
        if measure in self._measures:
            return

        # not in this document, but already in a chain, disallow
        if measure.next_measure is not None or measure.prev_measure is not None:
            raise ValueError("Measure is already in a chain.")

        # lookup current last measure or None
        last: Measure | None = self._measures[-1] if self._measures else None
        self._link_between(measure=measure, prev=last, nxt=None, sink=sink)

        sink.list_append(self._measures, measure)

    def remove_measure(
        self,
        *,
        measure: Measure,
        sink: MutationSink = DIRECT_SINK,
    ) -> None:
        # idempotency
        if measure not in self._measures:
            return

        self._remove_from_chain(measure=measure, sink=sink)

        sink.list_remove(self._measures, measure)

    # inserts a measure into the chain, linking it to the previous and next measures
    # no checks of belonging to the document are performed because the method is private
    def _link_between(
        self,
        *,
        measure: Measure,
        prev: Measure | None,
        nxt: Measure | None,
        sink: MutationSink = DIRECT_SINK,
    ) -> None:
        measure.set_prev(prev_measure=prev, sink=sink)
        measure.set_next(next_measure=nxt, sink=sink)

        if prev is not None:
            prev.set_next(next_measure=measure, sink=sink)

        if nxt is not None:
            nxt.set_prev(prev_measure=measure, sink=sink)

    # removes a measure from the chain, linking the previous and next measures to each other
    # no checks of belonging to the document are performed because the method is private
    def _remove_from_chain(
        self,
        *,
        measure: Measure,
        sink: MutationSink = DIRECT_SINK,
    ) -> None:
        prev: Measure | None = measure.prev_measure
        nxt: Measure | None = measure.next_measure

        if prev is not None:
            prev.set_next(next_measure=nxt, sink=sink)

        if nxt is not None:
            nxt.set_prev(prev_measure=prev, sink=sink)

        measure.set_prev(prev_measure=None, sink=sink)
        measure.set_next(next_measure=None, sink=sink)
