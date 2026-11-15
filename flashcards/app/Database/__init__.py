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
    @abstractmethod
    def db_start(self) -> None:
        ...

    # --- Exams ---

    @abstractmethod
    def list_exams(self) -> list[ExamResponse]:
        ...

    @abstractmethod
    def get_exam(self, exam_id: int) -> ExamResponse:
        ...

    @abstractmethod
    def create_exam(self, data: ExamCreate) -> ExamResponse:
        ...

    @abstractmethod
    def update_exam(self, exam_id: int, data: ExamUpdate) -> ExamResponse:
        ...

    @abstractmethod
    def delete_exam(self, exam_id: int) -> None:
        ...

    # --- Decks ---

    @abstractmethod
    def list_decks(self, exam_id: int | None) -> list[DeckResponse]:
        ...

    @abstractmethod
    def list_all_decks(self) -> list[DeckResponse]:
        ...

    @abstractmethod
    def get_deck(self, deck_id: int) -> DeckResponse:
        ...

    @abstractmethod
    def create_deck(self, data: DeckCreate) -> DeckResponse:
        ...

    @abstractmethod
    def update_deck(self, deck_id: int, data: DeckUpdate) -> DeckResponse:
        ...

    @abstractmethod
    def delete_deck(self, deck_id: int) -> None:
        ...

    # --- Cards ---

    @abstractmethod
    def list_cards(self, deck_id: int) -> list[CardResponse]:
        ...

    @abstractmethod
    def list_due_cards(
        self, now: AwareDatetime | None = None
    ) -> list[CardResponse]:
        ...

    @abstractmethod
    def list_due_cards_by_exam(
        self, exam_id: int, now: AwareDatetime | None = None
    ) -> list[CardResponse]:
        ...

    @abstractmethod
    def list_due_cards_by_deck(
        self, deck_id: int, now: AwareDatetime | None = None
    ) -> list[CardResponse]:
        ...

    @abstractmethod
    def get_card(self, card_id: int) -> CardResponse:
        ...

    @abstractmethod
    def create_card(self, data: CardCreate) -> CardResponse:
        ...

    @abstractmethod
    def update_card(self, card_id: int, data: CardUpdate) -> CardResponse:
        ...

    @abstractmethod
    def delete_card(self, card_id: int) -> None:
        ...

    # --- Reviews ---

    @abstractmethod
    def save_review(
        self, card_id: int, schedule: CardSchedule, review: ReviewLogCreate
    ) -> CardResponse:
        ...

    @abstractmethod
    def list_review_logs(self, card_id: int) -> list[ReviewLogResponse]:
        ...


def get_database() -> DatabaseAPI:
    from .SQLlite import SQLiteDatabase

    return SQLiteDatabase()
