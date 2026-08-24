class FrameMismatchError(Exception):
    """Raised when an operation is asked to combine coordinates of different frames.

    Comparing or subtracting two spans only means something inside one coordinate
    space; doing it across frames is a caller bug, not a musical situation.
    """


class UnreachableFrameError(Exception):
    """Raised when there is no path between two frames — they belong to different
    documents, so no conversion exists.

    This is the only genuine geometric impossibility. A span crossing a barline or
    overflowing a group is NOT this: it is a fact the caller decides about.
    """


class OutsideFrameError(Exception):
    """Raised when a coordinate is projected into a frame that does not hold it.

    Asking for the coordinates of a point in a space it never falls into has no
    answer. When crossing IS expected, ask what the span meets instead of forcing
    it into one frame.
    """
