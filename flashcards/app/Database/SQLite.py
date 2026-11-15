from datetime import datetime, timezone
from pathlib import Path

from pydantic import AwareDatetime
from sqlalchemy import create_engine, event, func, make_url, or_, select, update
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
        cls.remove_unused_images()

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
            images = cls._image_names(
                session, select(Card.front_image, Card.back_image).join(Deck).where(Deck.exam_id == exam_id)
            )
            session.delete(exam)
            session.commit()
            cls._remove_unused_images(images)

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
            images = cls._image_names(
                session, select(Card.front_image, Card.back_image).where(Card.deck_id == deck_id)
            )
            session.delete(deck)
            session.commit()
            cls._remove_unused_images(images)

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
    def list_cards_by_exam(cls, exam_id: int) -> list[CardResponse]:
        with cls._session() as session:
            if session.get(Exam, exam_id) is None:
                raise NotFoundError("Exam", exam_id)
            cards = session.scalars(
                select(Card)
                .join(Deck)
                .where(Deck.exam_id == exam_id)
                .order_by(Deck.id, Card.position)
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
            cls._check_images_exist((data.front_image, data.back_image))
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
            changes = data.model_dump(exclude_unset=True)
            cls._check_images_exist(changes.get(field) for field in ("front_image", "back_image"))
            images = {card.front_image, card.back_image}
            for field, value in changes.items():
                setattr(card, field, value)
            session.commit()
            session.refresh(card)
            cls._remove_unused_images(images - {card.front_image, card.back_image})
            return CardResponse.model_validate(card)

    @classmethod
    def reposition_card(cls, card_id: int, position: int) -> CardResponse:
        with cls._session() as session:
            card = session.get(Card, card_id)
            if card is None:
                raise NotFoundError("Card", card_id)
            old = card.position
            new = max(0, min(position, cls._card_count(session, card.deck_id) - 1))
            if new < old:
                session.execute(
                    update(Card)
                    .where(Card.deck_id == card.deck_id, Card.position >= new, Card.position < old)
                    .values(position=Card.position + 1)
                )
            elif new > old:
                session.execute(
                    update(Card)
                    .where(Card.deck_id == card.deck_id, Card.position > old, Card.position <= new)
                    .values(position=Card.position - 1)
                )
            card.position = new
            session.commit()
            session.refresh(card)
            return CardResponse.model_validate(card)

    @classmethod
    def delete_card(cls, card_id: int) -> None:
        with cls._session() as session:
            card = session.get(Card, card_id)
            if card is None:
                raise NotFoundError("Card", card_id)
            deck_id, position = card.deck_id, card.position
            images = {card.front_image, card.back_image}
            session.delete(card)
            session.flush()
            session.execute(
                update(Card)
                .where(Card.deck_id == deck_id, Card.position > position)
                .values(position=Card.position - 1)
            )
            session.commit()
            cls._remove_unused_images(images)

    @staticmethod
    def _card_count(session: Session, deck_id: int) -> int:
        return session.scalar(select(func.count()).select_from(Card).where(Card.deck_id == deck_id))

    @staticmethod
    def _image_names(session: Session, query) -> set[str]:
        return {name for row in session.execute(query) for name in row}

    # --- Images ---

    @classmethod
    def image_in_use(cls, name: str) -> bool:
        with cls._session() as session:
            return session.scalar(
                select(
                    select(Card.id)
                    .where(or_(Card.front_image == name, Card.back_image == name))
                    .exists()
                )
            )

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

    @classmethod
    def list_review_logs_by_exam(cls, exam_id: int) -> list[ReviewLogResponse]:
        with cls._session() as session:
            if session.get(Exam, exam_id) is None:
                raise NotFoundError("Exam", exam_id)
            logs = session.scalars(
                select(ReviewLog)
                .join(Card)
                .join(Deck)
                .where(Deck.exam_id == exam_id)
                .order_by(ReviewLog.reviewed_at, ReviewLog.id)
            )
            return [ReviewLogResponse.model_validate(l) for l in logs]

    # --- Import ---

    @classmethod
    def import_exam(cls, data: ExamImport) -> ExamResponse:
        for deck in data.decks:
            cls._check_card_images(deck)
        with cls._session() as session:
            exam = Exam(**data.model_dump(exclude={"decks"}))
            exam.decks = [cls._build_deck(d) for d in data.decks]
            session.add(exam)
            session.commit()
            session.refresh(exam)
            return ExamResponse.model_validate(exam)

    @classmethod
    def import_deck(cls, data: DeckImport, exam_id: int | None) -> DeckResponse:
        with cls._session() as session:
            if exam_id is not None and session.get(Exam, exam_id) is None:
                raise NotFoundError("Exam", exam_id)
            cls._check_card_images(data)
            deck = cls._build_deck(data)
            deck.exam_id = exam_id
            session.add(deck)
            session.commit()
            session.refresh(deck)
            return DeckResponse.model_validate(deck)

    @classmethod
    def _check_card_images(cls, data: DeckImport) -> None:
        cls._check_images_exist(name for c in data.cards for name in (c.front_image, c.back_image))

    @staticmethod
    def _build_deck(data: DeckImport) -> Deck:
        deck = Deck(**data.model_dump(exclude={"cards"}))
        deck.cards = [
            Card(**card.model_dump(), position=position)
            for position, card in enumerate(data.cards)
        ]
        return deck
