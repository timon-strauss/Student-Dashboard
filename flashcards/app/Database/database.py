import re
from abc import ABC, abstractmethod
from collections.abc import Iterable
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

from pydantic import AwareDatetime

from .exceptions import NotFoundError
from .schemas import (
    CardCreate,
    CardResponse,
    CardSchedule,
    CardUpdate,
    DeckCreate,
    DeckImport,
    DeckResponse,
    DeckUpdate,
    ExamCreate,
    ExamImport,
    ExamResponse,
    ExamUpdate,
    ReviewLogCreate,
    ReviewLogResponse,
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]

DATA_DIR = PROJECT_ROOT / "data"
UPLOAD_DIR = PROJECT_ROOT / "uploads"
DATABASE_URL = f"sqlite:///{DATA_DIR / 'flashcards.db'}"

IMAGE_EXTENSION = re.compile(r"^\.[A-Za-z0-9]+$")
SAVED_IMAGE_NAME = re.compile(r"^[0-9a-f]{32}\.[a-z0-9]+$")
UNUSED_IMAGE_MAX_AGE = timedelta(hours=1)


def create_folders() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


class DatabaseAPI(ABC):
    @classmethod
    @abstractmethod
    def db_start(cls) -> None:
        ...

    # --- Exams ---

    @classmethod
    @abstractmethod
    def list_exams(cls) -> list[ExamResponse]:
        ...

    @classmethod
    @abstractmethod
    def get_exam(cls, exam_id: int) -> ExamResponse:
        ...

    @classmethod
    @abstractmethod
    def create_exam(cls, data: ExamCreate) -> ExamResponse:
        ...

    @classmethod
    @abstractmethod
    def update_exam(cls, exam_id: int, data: ExamUpdate) -> ExamResponse:
        ...

    @classmethod
    @abstractmethod
    def delete_exam(cls, exam_id: int) -> None:
        ...

    # --- Decks ---

    @classmethod
    @abstractmethod
    def list_decks(cls, exam_id: int | None) -> list[DeckResponse]:
        ...

    @classmethod
    @abstractmethod
    def list_all_decks(cls) -> list[DeckResponse]:
        ...

    @classmethod
    @abstractmethod
    def get_deck(cls, deck_id: int) -> DeckResponse:
        ...

    @classmethod
    @abstractmethod
    def create_deck(cls, data: DeckCreate) -> DeckResponse:
        ...

    @classmethod
    @abstractmethod
    def update_deck(cls, deck_id: int, data: DeckUpdate) -> DeckResponse:
        ...

    @classmethod
    @abstractmethod
    def delete_deck(cls, deck_id: int) -> None:
        ...

    # --- Cards ---

    @classmethod
    @abstractmethod
    def list_cards(cls, deck_id: int) -> list[CardResponse]:
        ...

    @classmethod
    @abstractmethod
    def list_cards_by_exam(cls, exam_id: int) -> list[CardResponse]:
        ...

    @classmethod
    @abstractmethod
    def list_due_cards(
        cls, now: AwareDatetime | None = None
    ) -> list[CardResponse]:
        ...

    @classmethod
    @abstractmethod
    def list_due_cards_by_exam(
        cls, exam_id: int, now: AwareDatetime | None = None
    ) -> list[CardResponse]:
        ...

    @classmethod
    @abstractmethod
    def list_due_cards_by_deck(
        cls, deck_id: int, now: AwareDatetime | None = None
    ) -> list[CardResponse]:
        ...

    @classmethod
    @abstractmethod
    def get_card(cls, card_id: int) -> CardResponse:
        ...

    @classmethod
    @abstractmethod
    def create_card(cls, data: CardCreate) -> CardResponse:
        ...

    @classmethod
    @abstractmethod
    def update_card(cls, card_id: int, data: CardUpdate) -> CardResponse:
        ...

    @classmethod
    @abstractmethod
    def reposition_card(cls, card_id: int, position: int) -> CardResponse:
        ...

    @classmethod
    @abstractmethod
    def delete_card(cls, card_id: int) -> None:
        ...

    # --- Reviews ---

    @classmethod
    @abstractmethod
    def save_review(
        cls, card_id: int, schedule: CardSchedule, review: ReviewLogCreate
    ) -> CardResponse:
        ...

    @classmethod
    @abstractmethod
    def list_review_logs(cls, card_id: int) -> list[ReviewLogResponse]:
        ...

    @classmethod
    @abstractmethod
    def list_review_logs_by_exam(cls, exam_id: int) -> list[ReviewLogResponse]:
        ...

    # --- Import ---

    @classmethod
    @abstractmethod
    def import_exam(cls, data: ExamImport) -> ExamResponse:
        ...

    @classmethod
    @abstractmethod
    def import_deck(cls, data: DeckImport, exam_id: int | None) -> DeckResponse:
        ...

    # --- Images ---

    @classmethod
    @abstractmethod
    def image_in_use(cls, name: str) -> bool:
        ...

    @classmethod
    def save_image(cls, data: bytes, extension: str) -> str:
        if not IMAGE_EXTENSION.match(extension):
            raise ValueError(f"Invalid image extension: {extension!r}")
        name = f"{uuid4().hex}{extension.lower()}"
        with open(UPLOAD_DIR / name, "xb") as file:
            file.write(data)
        return name

    @classmethod
    def get_image_path(cls, name: str) -> Path:
        path = cls._upload_path(name)
        if path is None or not path.is_file():
            raise NotFoundError("Image", name)
        return path

    @classmethod
    def remove_unused_images(cls, older_than: timedelta = UNUSED_IMAGE_MAX_AGE) -> None:
        cutoff = (datetime.now(timezone.utc) - older_than).timestamp()
        for path in UPLOAD_DIR.iterdir():
            if not SAVED_IMAGE_NAME.match(path.name):
                continue
            try:
                expired = path.is_file() and path.stat().st_mtime < cutoff
            except OSError:
                continue
            if expired and not cls.image_in_use(path.name):
                cls._unlink(path)

    @classmethod
    def _check_images_exist(cls, names: Iterable[str | None]) -> None:
        for name in names:
            if name is not None:
                cls.get_image_path(name)

    @classmethod
    def _remove_unused_images(cls, names: set[str | None]) -> None:
        for name in names - {None}:
            path = cls._upload_path(name)
            if path is not None and not cls.image_in_use(name):
                cls._unlink(path)

    @staticmethod
    def _unlink(path: Path) -> None:
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass

    @staticmethod
    def _upload_path(name: str) -> Path | None:
        upload_dir = UPLOAD_DIR.resolve()
        path = (upload_dir / name).resolve()
        return path if path.parent == upload_dir else None
