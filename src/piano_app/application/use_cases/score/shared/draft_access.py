from piano_app.application.errors import DraftNotFoundError
from piano_app.application.ports import DraftStore
from piano_app.application.ports.score import VersionedDraftDocument


async def require_accessible_draft(
    *,
    storage: DraftStore,
    draft_id: str,
    viewer_id: str,
) -> VersionedDraftDocument:
    versioned: VersionedDraftDocument | None = await storage.get(draft_id=draft_id)

    if versioned is None:
        raise DraftNotFoundError(draft_id=draft_id)

    if versioned.meta.author_id != viewer_id:
        raise DraftNotFoundError(draft_id=draft_id)

    return versioned
