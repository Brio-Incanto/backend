from collections.abc import Sequence
from dataclasses import dataclass

from piano_app.domain.score.models.material.carrier import NoteCarrier
from piano_app.domain.score.models.mutation_sink import DIRECT_SINK, MutationSink
from piano_app.domain.score.models.notation import ArpeggioType

from .carrier import CarrierGroupRelation


@dataclass(slots=True, kw_only=True, eq=False)
class Arpeggio(CarrierGroupRelation[NoteCarrier]):
    """An arpeggio over note carriers containing at least two notes in total."""

    arpeggio_type: ArpeggioType = ArpeggioType.ARPEGGIATO

    def __post_init__(self) -> None:
        super().__post_init__()

        if sum(len(carrier.notes) for carrier in self.members) < 2:
            raise ValueError("Arpeggio must contain at least two notes.")

    @classmethod
    def create(
        cls,
        *,
        note_carriers: Sequence[NoteCarrier],
        arpeggio_type: ArpeggioType = ArpeggioType.ARPEGGIATO,
        sink: MutationSink = DIRECT_SINK,
    ) -> Arpeggio:
        arpeggio: Arpeggio = cls(
            _members=tuple(note_carriers),
            arpeggio_type=arpeggio_type,
        )
        arpeggio.attach(sink=sink)
        return arpeggio
