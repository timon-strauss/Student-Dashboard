from datetime import datetime, timezone

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.orm import relationship
from sqlalchemy.types import TypeDecorator

from .database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class UTCDateTime(TypeDecorator):
    """Stores datetimes as naive UTC and returns them timezone-aware (UTC).

    SQLite drops tzinfo, but py-fsrs requires aware UTC datetimes
    (comparing naive and aware datetimes raises a TypeError).
    """

    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if value.tzinfo is None:
            raise ValueError("UTCDateTime requires a timezone-aware datetime")
        return value.astimezone(timezone.utc).replace(tzinfo=None)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return value.replace(tzinfo=timezone.utc)


class Exam(Base):
    __tablename__ = "exams"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    exam_date = Column(UTCDateTime, nullable=False)

    decks = relationship(
        "Deck", back_populates="exam", cascade="all, delete", passive_deletes=True
    )


class Deck(Base):
    __tablename__ = "decks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    exam_id = Column(
        Integer, ForeignKey("exams.id", ondelete="CASCADE"), nullable=True, index=True
    )
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)

    exam = relationship("Exam", back_populates="decks")
    cards = relationship(
        "Card",
        back_populates="deck",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Card(Base):
    __tablename__ = "cards"
    __table_args__ = (
        CheckConstraint("state IN (1, 2, 3)", name="ck_cards_state"),
        # due cards of one deck, ordered by due date
        Index("ix_cards_deck_id_due", "deck_id", "due"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    deck_id = Column(
        Integer, ForeignKey("decks.id", ondelete="CASCADE"), nullable=False
    )
    front = Column(String, nullable=False)
    front_image = Column(String, nullable=True)
    back = Column(String, nullable=False)
    back_image = Column(String, nullable=True)
    position = Column(Integer, nullable=False, default=0)

    # FSRS scheduling state (mirrors fsrs.Card)
    # state: 1 = Learning, 2 = Review, 3 = Relearning (new card = Learning without last_review)
    state = Column(Integer, nullable=False, default=1)
    # index of the current (re)learning step; None once the card is in Review
    step = Column(Integer, nullable=True, default=0)
    # None until the first review
    stability = Column(Float, nullable=True)
    difficulty = Column(Float, nullable=True)
    # new cards are due immediately
    due = Column(UTCDateTime, nullable=False, default=utcnow, index=True)
    last_review = Column(UTCDateTime, nullable=True)

    deck = relationship("Deck", back_populates="cards")
    review_logs = relationship(
        "ReviewLog",
        back_populates="card",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class ReviewLog(Base):
    __tablename__ = "review_logs"
    __table_args__ = (
        CheckConstraint("rating IN (1, 2, 3, 4)", name="ck_review_logs_rating"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    card_id = Column(
        Integer,
        ForeignKey("cards.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # rating: 1 = Again, 2 = Hard, 3 = Good, 4 = Easy
    rating = Column(Integer, nullable=False)
    reviewed_at = Column(UTCDateTime, nullable=False, default=utcnow)

    card = relationship("Card", back_populates="review_logs")
