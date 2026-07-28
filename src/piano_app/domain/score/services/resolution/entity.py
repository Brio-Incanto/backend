import dataclasses

from piano_app.domain.score.models import ScoreDocument, ScoreEntity


class ScoreEntityResolver:
    """Resolves raw entity ids to the live entities of a score."""

    def __init__(self, *, document: ScoreDocument) -> None:
        self._document = document

    def resolve(self, *, ids: set[str]) -> dict[str, ScoreEntity]:
        """Return the requested entities keyed by id. Raise if some id is not found."""
        found: dict[str, ScoreEntity] = {}
        seen: set[str] = set()
        stack: list[ScoreEntity] = []

        def schedule_children_of(parent: ScoreEntity | ScoreDocument) -> None:
            for child_entity in unpack(parent):
                if child_entity.id not in seen:
                    seen.add(child_entity.id)
                    stack.append(child_entity)

        def unpack(parent: ScoreEntity | ScoreDocument) -> list[ScoreEntity]:
            child_entities: list[ScoreEntity] = []
            for field in dataclasses.fields(parent):
                child_entities.extend(self._flatten(getattr(parent, field.name)))

            return child_entities

        schedule_children_of(self._document)

        while stack:
            entity: ScoreEntity = stack.pop()

            # register matching entities
            if entity.id in ids:
                found[entity.id] = entity

                # tiny optimization here, stop if all ids were found
                if len(found) == len(ids):
                    break

            # keep searching deeper for children
            schedule_children_of(entity)

        # raise if not all ids were found here
        if len(found) != len(ids):
            raise ValueError(f"Could not resolve all ids: {ids - found.keys()}")

        return found

    @staticmethod
    def _flatten(value: object) -> list[ScoreEntity]:
        """Flatten a field value to the entities it holds, recursing through the
        standard containers (list/tuple/set/dict). A ``ScoreEntity`` is terminal.
        """
        entities: list[ScoreEntity] = []
        if isinstance(value, ScoreEntity):
            entities.append(value)
        elif isinstance(value, list | tuple | set):
            for item in value:
                entities.extend(ScoreEntityResolver._flatten(item))
        elif isinstance(value, dict):
            for item in value.values():
                entities.extend(ScoreEntityResolver._flatten(item))

        return entities
