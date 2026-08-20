from pathlib import Path

_SCRIPTS_DIR: Path = Path(__file__).parent / "scripts"


def _load(name: str) -> str:
    return (_SCRIPTS_DIR / name).read_text()


# Used by BOTH RedisDraftHistory and RedisDraftCache (get/commit/undo/redo are
# identical hot-tier mechanics regardless of which port a class satisfies) —
# scripts owned by only one of them live in that adapter's own file instead
# (RedisDraftHistory: _CREATE_SCRIPT / _LIST_BY_AUTHOR_SCRIPT;
# RedisDraftCache: _HYDRATE_SCRIPT / _LOAD_SNAPSHOT_SCRIPT).
_GET_SCRIPT: str = _load("get.lua")
_COMMIT_SCRIPT: str = _load("commit.lua")
_UNDO_SCRIPT: str = _load("undo.lua")
_REDO_SCRIPT: str = _load("redo.lua")
