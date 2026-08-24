from dataclasses import dataclass
from fractions import Fraction


@dataclass(frozen=True, slots=True, kw_only=True)
class Transform:
    """The affine step from one frame's coordinates into its parent's.

    ``value_in_parent = value_in_frame * scale + offset``, where ``scale`` is the
    frame's compression (a tuplet's occupied / written) and ``offset`` is where the
    frame begins in its parent. A measure is the degenerate case ``scale == 1``: it
    shifts without compressing.

    Affine composed with affine is affine, so a whole chain of frames collapses into
    one pair — which is what makes an arbitrary frame-to-frame conversion a single
    multiply-add rather than a tree walk.
    """

    scale: Fraction
    offset: Fraction

    def __post_init__(self) -> None:
        # a non-positive scale would mirror or collapse the space, which no rhythmic
        # nesting can express
        if self.scale <= 0:
            raise ValueError("Transform scale must be positive.")

    @classmethod
    def identity(cls) -> Transform:
        return cls(scale=Fraction(1), offset=Fraction(0))

    @classmethod
    def of_shift(cls, *, offset: Fraction) -> Transform:
        """A pure shift — the measure case, where the space is not compressed."""
        return cls(scale=Fraction(1), offset=offset)

    @classmethod
    def of_nesting(
        cls,
        *,
        written: Fraction,
        occupied: Fraction,
        offset: Fraction,
    ) -> Transform:
        """A tuplet step: ``occupied / written`` is how much the interior is squeezed
        to fit the room the group takes in its parent."""
        if written <= 0:
            raise ValueError("Written size must be positive.")

        return cls(scale=occupied / written, offset=offset)

    def then(self, outer: Transform) -> Transform:
        """Compose apply ``self`` first, then ``outer``."""
        return Transform(
            scale=outer.scale * self.scale,
            offset=outer.scale * self.offset + outer.offset,
        )

    def inverse(self) -> Transform:
        """The step back down. Descent is not a second implementation of the math."""
        return Transform(
            scale=1 / self.scale,
            offset=-self.offset / self.scale,
        )

    def apply_position(self, value: Fraction) -> Fraction:
        """Map a location, both the scale and the offset apply."""
        return value * self.scale + self.offset

    def apply_length(self, value: Fraction) -> Fraction:
        """Map a displacement, only the scale applies.

        A length is the difference of two locations, and the offsets cancel in that
        difference. This is why a size never needs an offset lookup while a position
        always does.
        """
        return value * self.scale
