from pathlib import Path

from dotenv import load_dotenv
from pydantic import ValidationError

from .models import Settings


def load_environment() -> None:
    project_root: Path = Path(__file__).resolve().parents[4]
    dotenv_path: Path = project_root / ".env"

    load_dotenv(dotenv_path=dotenv_path, override=False)


def load_settings() -> Settings:
    try:
        return Settings()
    except ValidationError as exc:
        raise RuntimeError("Failed to load application settings") from exc
