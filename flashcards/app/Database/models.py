from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, DateTime, Float, ForeignKey, Index
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import TypeDecorator


class Base(DeclarativeBase):
    pass


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

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str]
    description: Mapped[str | None]
    exam_date: Mapped[datetime] = mapped_column(UTCDateTime)

    decks: Mapped[list["Deck"]] = relationship(
        back_populates="exam", cascade="all, delete", passive_deletes=True
    )


class Deck(Base):
    __tablename__ = "decks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    exam_id: Mapped[int | None] = mapped_column(
        ForeignKey("exams.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str]
    description: Mapped[str | None]

    exam: Mapped["Exam | None"] = relationship(back_populates="decks")
    cards: Mapped[list["Card"]] = relationship(
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

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    deck_id: Mapped[int] = mapped_column(ForeignKey("decks.id", ondelete="CASCADE"))
    front: Mapped[str]
    front_image: Mapped[str | None]
    back: Mapped[str]
    back_image: Mapped[str | None]
    position: Mapped[int] = mapped_column(default=0)

    # FSRS scheduling state (mirrors fsrs.Card)
    # state: 1 = Learning, 2 = Review, 3 = Relearning (new card = Learning without last_review)
    state: Mapped[int] = mapped_column(default=1)
    # index of the current (re)learning step; None once the card is in Review
    step: Mapped[int | None] = mapped_column(default=0)
    # None until the first review
    stability: Mapped[float | None] = mapped_column(Float)
    difficulty: Mapped[float | None] = mapped_column(Float)
    # new cards are due immediately
    due: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow, index=True)
    last_review: Mapped[datetime | None] = mapped_column(UTCDateTime)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)

    deck: Mapped["Deck"] = relationship(back_populates="cards")
    review_logs: Mapped[list["ReviewLog"]] = relationship(
        back_populates="card",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class ReviewLog(Base):
    __tablename__ = "review_logs"
    __table_args__ = (
        CheckConstraint("rating IN (1, 2, 3, 4)", name="ck_review_logs_rating"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    card_id: Mapped[int] = mapped_column(
        ForeignKey("cards.id", ondelete="CASCADE"), index=True
    )
    # rating: 1 = Again, 2 = Hard, 3 = Good, 4 = Easy
    rating: Mapped[int]
    reviewed_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)

    card: Mapped["Card"] = relationship(back_populates="review_logs")
