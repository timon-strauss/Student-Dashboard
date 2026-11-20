from datetime import timedelta, timezone

import pytest

from app.Database import NotFoundError
from app.Database.models import Card, Deck, ReviewLog
from app.Database.schemas import ExamCreate, ExamResponse, ExamUpdate, Rating, ReviewLogCreate

from .conftest import NOW


def test_create_returns_persisted_exam(db):
    created = db.create_exam(ExamCreate(name="Mathe", description="Analysis", exam_date=NOW))

    assert isinstance(created, ExamResponse)
    assert created.id is not None
    assert db.get_exam(created.id) == created


def test_create_assigns_unique_ids(make_exam):
    assert make_exam().id != make_exam().id


def test_create_normalizes_timezone_to_utc(db):
    local = NOW.astimezone(timezone(timedelta(hours=2)))

    created = db.create_exam(ExamCreate(name="x", exam_date=local))

    assert created.exam_date == NOW
    assert created.exam_date.utcoffset() == timedelta(0)


def test_list_empty(db):
    assert db.list_exams() == []


def test_list_ordered_by_exam_date(make_exam, db):
    late = make_exam(name="late", exam_date=NOW + timedelta(days=10))
    early = make_exam(name="early", exam_date=NOW + timedelta(days=1))
    middle = make_exam(name="middle", exam_date=NOW + timedelta(days=5))

    assert [e.id for e in db.list_exams()] == [early.id, middle.id, late.id]


def test_get_missing_raises(db):
    with pytest.raises(NotFoundError) as exc:
        db.get_exam(123)

    assert exc.value.entity == "Exam"
    assert exc.value.entity_id == 123


def test_update_partial_keeps_other_fields(make_exam, db):
    exam = make_exam(name="alt", description="desc")

    updated = db.update_exam(exam.id, ExamUpdate(name="neu"))

    assert updated.name == "neu"
    assert updated.description == "desc"
    assert updated.exam_date == exam.exam_date
    assert db.get_exam(exam.id) == updated


def test_update_all_fields(make_exam, db):
    exam = make_exam()
    new_date = NOW + timedelta(days=99)

    updated = db.update_exam(
        exam.id, ExamUpdate(name="n", description="d", exam_date=new_date)
    )

    assert (updated.name, updated.description, updated.exam_date) == ("n", "d", new_date)


def test_update_can_clear_description(make_exam, db):
    exam = make_exam(description="desc")

    assert db.update_exam(exam.id, ExamUpdate(description=None)).description is None


def test_update_empty_is_noop(make_exam, db):
    exam = make_exam()

    assert db.update_exam(exam.id, ExamUpdate()) == exam


def test_update_missing_raises(db):
    with pytest.raises(NotFoundError):
        db.update_exam(1, ExamUpdate(name="x"))


def test_delete(make_exam, db):
    keep = make_exam(name="keep")
    gone = make_exam(name="gone")

    db.delete_exam(gone.id)

    assert db.list_exams() == [keep]
    with pytest.raises(NotFoundError):
        db.get_exam(gone.id)


def test_delete_missing_raises(db):
    with pytest.raises(NotFoundError):
        db.delete_exam(1)


def test_delete_cascades_to_decks_cards_and_reviews(make_exam, make_deck, make_card, db):
    exam = make_exam()
    other_exam = make_exam(name="other")
    deck = make_deck(exam_id=exam.id)
    other_deck = make_deck(exam_id=other_exam.id)
    free_deck = make_deck(exam_id=None)
    card = make_card(deck.id)
    other_card = make_card(other_deck.id)
    db.save_review(
        card.id,
        db.get_card(card.id),
        ReviewLogCreate(rating=Rating.GOOD, reviewed_at=NOW),
    )

    db.delete_exam(exam.id)

    assert {d.id for d in db.list_all_decks()} == {other_deck.id, free_deck.id}
    with pytest.raises(NotFoundError):
        db.get_card(card.id)
    assert db.get_card(other_card.id) == other_card
    with db._session() as session:
        assert session.query(Deck).filter_by(id=deck.id).count() == 0
        assert session.query(Card).filter_by(id=card.id).count() == 0
        assert session.query(ReviewLog).count() == 0
