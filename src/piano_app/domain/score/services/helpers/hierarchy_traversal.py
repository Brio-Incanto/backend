from piano_app.domain.score.models.structural.rhythm import (
    GroupRhythmicContainer,
    LeafRhythmicContainer,
)
from piano_app.domain.score.models.structural.rhythm.metric.parent import RhythmicContainerParent


def flatten(
    parent: RhythmicContainerParent,
) -> list[LeafRhythmicContainer]:
    flattened: list[LeafRhythmicContainer] = []
    for child in parent.children:
        if isinstance(child, LeafRhythmicContainer):
            flattened.append(child)
        elif isinstance(child, GroupRhythmicContainer):
            flattened.extend(flatten(child))
        else:
            raise TypeError(f"Unsupported rhythmic container type: {type(child).__name__}.")

    return flattened
