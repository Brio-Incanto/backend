from .author import build_authors_router
from .catalog import build_scores_router
from .draft import build_draft_router
from .edit import build_edit_router
from .save import build_save_router

__all__ = (
    "build_authors_router",
    "build_draft_router",
    "build_edit_router",
    "build_save_router",
    "build_scores_router",
)
