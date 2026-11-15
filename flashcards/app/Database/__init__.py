from abc import ABC, abstractmethod

from pydantic import AwareDatetime

from .schemas import (
    CardCreate,
    CardResponse,
    CardSchedule,
    CardUpdate,
    DeckCreate,
    DeckResponse,
    DeckUpdate,
    ExamCreate,
    ExamResponse,
    ExamUpdate,
    ReviewLogCreate,
    ReviewLogResponse,
)

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

# Exposing the Database to Other modules
from .SQLlite import SQLiteDatabase

db: type[DatabaseAPI] = SQLiteDatabase