from dataclasses import dataclass


@dataclass(frozen=True, slots=True, kw_only=True)
class Pitch:
    """A pitch in a piano key. Value should be already with accidental consideration."""

    octave: int  # 0 is subcontra octave, 8 is 5-line octave
    step: int  # 0 is C, 11 is B

    def __post_init__(self) -> None:
        if self.step < 0 or self.step > 11:
            raise ValueError("Step must be between 0 and 11.")

        if self.octave < 0 or self.octave > 8:
            raise ValueError("Octave must be between 0 and 8.")

    # midi note number, A0 is 21, C0 is 12
    @property
    def midi_note(self) -> int:
        midi_zero_shift: int = 12
        return (self.octave * 12 + self.step) + midi_zero_shift
