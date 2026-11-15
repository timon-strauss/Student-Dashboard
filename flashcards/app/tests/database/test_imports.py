from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.exc import IntegrityError

from Database import NotFoundError
from Database.models import Card, Deck, Exam
from Database.schemas import (
    CardContent,
    CardState,
    DeckImport,
    DeckResponse,
    ExamImport,
    ExamResponse,
)

from .conftest import NOW


def deck_import(name="Deck", cards=("a", "b", "c")):
    return DeckImport(
        name=name,
        description=f"{name} desc",
        cards=[CardContent(front=f, back=f.upper(), front_image=f"{f}.png") for f in cards],
    )


def count(db, model):
    with db._session() as session:
        return session.query(model).count()


class TestImportExam:
    def test_creates_exam_decks_and_cards(self, db):
        before = datetime.now(timezone.utc)
        data = ExamImport(
            name="Mathe",
            description="d",
            exam_date=NOW,
            decks=[deck_import("Analysis"), deck_import("Algebra", cards=("x",))],
        )

        exam = db.import_exam(data)

        assert isinstance(exam, ExamResponse)
        assert (exam.name, exam.description, exam.exam_date) == ("Mathe", "d", NOW)
        decks = db.list_decks(exam.id)
        assert [(d.name, d.description) for d in decks] == [
            ("Analysis", "Analysis desc"),
            ("Algebra", "Algebra desc"),
        ]
        cards = db.list_cards(decks[0].id)
        assert [(c.front, c.back, c.front_image, c.back_image, c.position) for c in cards] == [
            ("a", "A", "a.png", None, 0),
            ("b", "B", "b.png", None, 1),
            ("c", "C", "c.png", None, 2),
        ]
        assert all(c.state is CardState.LEARNING and c.last_review is None for c in cards)
        assert all(c.created_at >= before - timedelta(seconds=1) for c in cards)
        assert [c.front for c in db.list_cards(decks[1].id)] == ["x"]

    def test_empty_exam(self, db):
        exam = db.import_exam(ExamImport(name="Leer", exam_date=NOW))

        assert db.list_decks(exam.id) == []

    def test_failure_leaves_nothing_behind(self, db):
        data = ExamImport(name="Mathe", exam_date=NOW, decks=[deck_import()])
        data.decks[0].cards[1].back = None

        with pytest.raises(IntegrityError):
            db.import_exam(data)

        assert (count(db, Exam), count(db, Deck), count(db, Card)) == (0, 0, 0)


class TestImportDeck:
    def test_into_exam(self, make_exam, db):
        exam = make_exam()

        deck = db.import_deck(deck_import(), exam.id)

        assert isinstance(deck, DeckResponse)
        assert deck.exam_id == exam.id
        assert db.list_decks(exam.id) == [deck]
        assert [(c.front, c.position) for c in db.list_cards(deck.id)] == [("a", 0), ("b", 1), ("c", 2)]

    def test_without_exam(self, db):
        deck = db.import_deck(deck_import(), None)

        assert deck.exam_id is None
        assert db.list_decks(None) == [deck]

    def test_missing_exam_raises_and_creates_nothing(self, db):
        with pytest.raises(NotFoundError) as exc:
            db.import_deck(deck_import(), 99)

        assert (exc.value.entity, exc.value.entity_id) == ("Exam", 99)
        assert (count(db, Deck), count(db, Card)) == (0, 0)

    def test_failure_leaves_nothing_behind(self, db):
        data = deck_import()
        data.cards[2].front = None

        with pytest.raises(IntegrityError):
            db.import_deck(data, None)

        assert (count(db, Deck), count(db, Card)) == (0, 0)

    def test_new_card_after_import_is_appended(self, make_card, db):
        deck = db.import_deck(deck_import(), None)

        assert make_card(deck.id).position == 3
