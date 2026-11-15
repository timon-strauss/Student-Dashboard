from datetime import datetime, timezone
from pathlib import Path

from pydantic import AwareDatetime
from sqlalchemy import create_engine, event, func, make_url, select
from sqlalchemy.orm import Session, sessionmaker

from .database import DATABASE_URL, PROJECT_ROOT, DatabaseAPI, create_folders
from .exceptions import DatabaseNotStartedError, NotFoundError
from .models import Base, Card, Deck, Exam, ReviewLog
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


class SQLiteDatabase(DatabaseAPI):
    _session_factory: sessionmaker | None = None

    @staticmethod
    def _enable_foreign_keys(connection, _):
        connection.execute("PRAGMA foreign_keys=ON")

    @classmethod
    def db_start(cls) -> None:
        create_folders()
        url = make_url(DATABASE_URL)
        if url.database and url.database != ":memory:":
            db_path = Path(url.database)
            if not db_path.is_absolute():
                db_path = (PROJECT_ROOT / db_path).resolve()
                url = url.set(database=str(db_path))
            db_path.parent.mkdir(parents=True, exist_ok=True)
        engine = create_engine(url)
        event.listen(engine, "connect", cls._enable_foreign_keys)
        Base.metadata.create_all(engine)
        cls._session_factory = sessionmaker(bind=engine)

    @classmethod
    def _session(cls) -> Session:
        if cls._session_factory is None:
            raise DatabaseNotStartedError()
        return cls._session_factory()

    # --- Exams ---

    @classmethod
    def list_exams(cls) -> list[ExamResponse]:
        with cls._session() as session:
            exams = session.scalars(select(Exam).order_by(Exam.exam_date))
            return [ExamResponse.model_validate(e) for e in exams]

    @classmethod
    def get_exam(cls, exam_id: int) -> ExamResponse:
        with cls._session() as session:
            exam = session.get(Exam, exam_id)
            if exam is None:
                raise NotFoundError("Exam", exam_id)
            return ExamResponse.model_validate(exam)

    @classmethod
    def create_exam(cls, data: ExamCreate) -> ExamResponse:
        with cls._session() as session:
            exam = Exam(**data.model_dump())
            session.add(exam)
            session.commit()
            session.refresh(exam)
            return ExamResponse.model_validate(exam)

    @classmethod
    def update_exam(cls, exam_id: int, data: ExamUpdate) -> ExamResponse:
        with cls._session() as session:
            exam = session.get(Exam, exam_id)
            if exam is None:
                raise NotFoundError("Exam", exam_id)
            for field, value in data.model_dump(exclude_unset=True).items():
                setattr(exam, field, value)
            session.commit()
            session.refresh(exam)
            return ExamResponse.model_validate(exam)

    @classmethod
    def delete_exam(cls, exam_id: int) -> None:
        with cls._session() as session:
            exam = session.get(Exam, exam_id)
            if exam is None:
                raise NotFoundError("Exam", exam_id)
            session.delete(exam)
            session.commit()

    # --- Decks ---

    @classmethod
    def list_decks(cls, exam_id: int | None) -> list[DeckResponse]:
        with cls._session() as session:
            if exam_id is not None and session.get(Exam, exam_id) is None:
                raise NotFoundError("Exam", exam_id)
            decks = session.scalars(select(Deck).where(Deck.exam_id == exam_id))
            return [DeckResponse.model_validate(d) for d in decks]

    @classmethod
    def list_all_decks(cls) -> list[DeckResponse]:
        with cls._session() as session:
            decks = session.scalars(select(Deck))
            return [DeckResponse.model_validate(d) for d in decks]

    @classmethod
    def get_deck(cls, deck_id: int) -> DeckResponse:
        with cls._session() as session:
            deck = session.get(Deck, deck_id)
            if deck is None:
                raise NotFoundError("Deck", deck_id)
            return DeckResponse.model_validate(deck)

    @classmethod
    def create_deck(cls, data: DeckCreate) -> DeckResponse:
        with cls._session() as session:
            if data.exam_id is not None and session.get(Exam, data.exam_id) is None:
                raise NotFoundError("Exam", data.exam_id)
            deck = Deck(**data.model_dump())
            session.add(deck)
            session.commit()
            session.refresh(deck)
            return DeckResponse.model_validate(deck)

    @classmethod
    def update_deck(cls, deck_id: int, data: DeckUpdate) -> DeckResponse:
        with cls._session() as session:
            deck = session.get(Deck, deck_id)
            if deck is None:
                raise NotFoundError("Deck", deck_id)
            changes = data.model_dump(exclude_unset=True)
            new_exam_id = changes.get("exam_id")
            if new_exam_id is not None and session.get(Exam, new_exam_id) is None:
                raise NotFoundError("Exam", new_exam_id)
            for field, value in changes.items():
                setattr(deck, field, value)
            session.commit()
            session.refresh(deck)
            return DeckResponse.model_validate(deck)

    @classmethod
    def delete_deck(cls, deck_id: int) -> None:
        with cls._session() as session:
            deck = session.get(Deck, deck_id)
            if deck is None:
                raise NotFoundError("Deck", deck_id)
            session.delete(deck)
            session.commit()

    # --- Cards ---

    @classmethod
    def list_cards(cls, deck_id: int) -> list[CardResponse]:
        with cls._session() as session:
            if session.get(Deck, deck_id) is None:
                raise NotFoundError("Deck", deck_id)
            cards = session.scalars(
                select(Card).where(Card.deck_id == deck_id).order_by(Card.position)
            )
            return [CardResponse.model_validate(c) for c in cards]

    @classmethod
    def list_due_cards(cls, now: AwareDatetime | None = None) -> list[CardResponse]:
        now = now or datetime.now(timezone.utc)
        with cls._session() as session:
            cards = session.scalars(
                select(Card).where(Card.due <= now).order_by(Card.due)
            )
            return [CardResponse.model_validate(c) for c in cards]

    @classmethod
    def list_due_cards_by_exam(
        cls, exam_id: int, now: AwareDatetime | None = None
    ) -> list[CardResponse]:
        now = now or datetime.now(timezone.utc)
        with cls._session() as session:
            if session.get(Exam, exam_id) is None:
                raise NotFoundError("Exam", exam_id)
            cards = session.scalars(
                select(Card)
                .join(Deck)
                .where(Deck.exam_id == exam_id, Card.due <= now)
                .order_by(Card.due)
            )
            return [CardResponse.model_validate(c) for c in cards]

    @classmethod
    def list_due_cards_by_deck(
        cls, deck_id: int, now: AwareDatetime | None = None
    ) -> list[CardResponse]:
        now = now or datetime.now(timezone.utc)
        with cls._session() as session:
            if session.get(Deck, deck_id) is None:
                raise NotFoundError("Deck", deck_id)
            cards = session.scalars(
                select(Card)
                .where(Card.deck_id == deck_id, Card.due <= now)
                .order_by(Card.due)
            )
            return [CardResponse.model_validate(c) for c in cards]

    @classmethod
    def get_card(cls, card_id: int) -> CardResponse:
        with cls._session() as session:
            card = session.get(Card, card_id)
            if card is None:
                raise NotFoundError("Card", card_id)
            return CardResponse.model_validate(card)

    @classmethod
    def create_card(cls, data: CardCreate) -> CardResponse:
        with cls._session() as session:
            if session.get(Deck, data.deck_id) is None:
                raise NotFoundError("Deck", data.deck_id)
            card = Card(**data.model_dump(), position=cls._card_count(session, data.deck_id))
            session.add(card)
            session.commit()
            session.refresh(card)
            return CardResponse.model_validate(card)

    @classmethod
    def update_card(cls, card_id: int, data: CardUpdate) -> CardResponse:
        with cls._session() as session:
            card = session.get(Card, card_id)
            if card is None:
                raise NotFoundError("Card", card_id)
            for field, value in data.model_dump(exclude_unset=True).items():
                setattr(card, field, value)
            session.commit()
            session.refresh(card)
            return CardResponse.model_validate(card)

    @classmethod
    def delete_card(cls, card_id: int) -> None:
        with cls._session() as session:
            card = session.get(Card, card_id)
            if card is None:
                raise NotFoundError("Card", card_id)
            session.delete(card)
            session.commit()

    @staticmethod
    def _card_count(session: Session, deck_id: int) -> int:
        return session.scalar(select(func.count()).select_from(Card).where(Card.deck_id == deck_id))

    # --- Reviews ---

    @classmethod
    def save_review(
        cls, card_id: int, schedule: CardSchedule, review: ReviewLogCreate
    ) -> CardResponse:
        with cls._session() as session:
            card = session.get(Card, card_id)
            if card is None:
                raise NotFoundError("Card", card_id)
            for field, value in schedule.model_dump().items():
                setattr(card, field, value)
            session.add(ReviewLog(card_id=card_id, **review.model_dump()))
            session.commit()
            session.refresh(card)
            return CardResponse.model_validate(card)

    @classmethod
    def list_review_logs(cls, card_id: int) -> list[ReviewLogResponse]:
        with cls._session() as session:
            if session.get(Card, card_id) is None:
                raise NotFoundError("Card", card_id)
            logs = session.scalars(
                select(ReviewLog)
                .where(ReviewLog.card_id == card_id)
                .order_by(ReviewLog.reviewed_at)
            )
            return [ReviewLogResponse.model_validate(l) for l in logs]
