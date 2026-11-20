from abc import ABC, abstractmethod
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]

DATA_DIR = PROJECT_ROOT / "data"
DATABASE_URL = f"sqlite:///{DATA_DIR / 'grades.db'}"


def create_folders() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


class DatabaseAPI(ABC):
    @classmethod
    @abstractmethod
    def db_start(cls) -> None:
        raise NotImplementedError
