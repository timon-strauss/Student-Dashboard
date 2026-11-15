import pytest

from Database import NotFoundError
from Database.models import ReviewLog
from Database.schemas import DeckCreate, DeckResponse, DeckUpdate, Rating, ReviewLogCreate

from .conftest import NOW


def test_create_with_exam(make_exam, db):
    exam = make_exam()

    deck = db.create_deck(DeckCreate(exam_id=exam.id, name="Kapitel 1", description="d"))

    assert isinstance(deck, DeckResponse)
    assert (deck.exam_id, deck.name, deck.description) == (exam.id, "Kapitel 1", "d")
    assert db.get_deck(deck.id) == deck


def test_create_without_exam(db):
    deck = db.create_deck(DeckCreate(name="frei"))

    assert deck.exam_id is None


def test_create_with_missing_exam_raises_and_persists_nothing(db):
    with pytest.raises(NotFoundError) as exc:
        db.create_deck(DeckCreate(exam_id=99, name="x"))

    assert (exc.value.entity, exc.value.entity_id) == ("Exam", 99)
    assert db.list_all_decks() == []


def test_get_missing_raises(db):
    with pytest.raises(NotFoundError) as exc:
        db.get_deck(5)

    assert exc.value.entity == "Deck"


def test_list_decks_filters_by_exam(make_exam, make_deck, db):
    exam_a = make_exam(name="a")
    exam_b = make_exam(name="b")
    a1 = make_deck(exam_id=exam_a.id)
    a2 = make_deck(exam_id=exam_a.id)
    make_deck(exam_id=exam_b.id)
    make_deck(exam_id=None)

    assert {d.id for d in db.list_decks(exam_a.id)} == {a1.id, a2.id}


def test_list_decks_none_returns_only_unassigned(make_exam, make_deck, db):
    exam = make_exam()
    make_deck(exam_id=exam.id)
    free = make_deck(exam_id=None)

    assert db.list_decks(None) == [free]


def test_list_decks_for_exam_without_decks(make_exam, db):
    assert db.list_decks(make_exam().id) == []


def test_list_decks_missing_exam_raises(db):
    with pytest.raises(NotFoundError):
        db.list_decks(42)


def test_list_all_decks(make_exam, make_deck, db):
    exam = make_exam()
    decks = [make_deck(exam_id=exam.id), make_deck(exam_id=None)]

    assert sorted(db.list_all_decks(), key=lambda d: d.id) == decks


def test_list_all_decks_empty(db):
    assert db.list_all_decks() == []


def test_update_partial(make_deck, db):
    deck = make_deck(name="alt", description="desc")

    updated = db.update_deck(deck.id, DeckUpdate(name="neu"))

    assert (updated.name, updated.description) == ("neu", "desc")
    assert db.get_deck(deck.id) == updated


def test_update_moves_deck_to_other_exam(make_exam, make_deck, db):
    old = make_exam(name="old")
    new = make_exam(name="new")
    deck = make_deck(exam_id=old.id)

    db.update_deck(deck.id, DeckUpdate(exam_id=new.id))

    assert db.list_decks(old.id) == []
    assert [d.id for d in db.list_decks(new.id)] == [deck.id]


def test_update_detaches_from_exam(make_exam, make_deck, db):
    deck = make_deck(exam_id=make_exam().id)

    updated = db.update_deck(deck.id, DeckUpdate(exam_id=None))

    assert updated.exam_id is None
    assert db.list_decks(None) == [updated]


def test_update_with_missing_exam_raises_and_keeps_deck(make_exam, make_deck, db):
    deck = make_deck(exam_id=make_exam().id, name="unchanged")

    with pytest.raises(NotFoundError) as exc:
        db.update_deck(deck.id, DeckUpdate(exam_id=99, name="changed"))

    assert exc.value.entity == "Exam"
    assert db.get_deck(deck.id) == deck


def test_update_missing_deck_raises(db):
    with pytest.raises(NotFoundError) as exc:
        db.update_deck(1, DeckUpdate(name="x"))

    assert exc.value.entity == "Deck"


def test_delete(make_deck, db):
    keep = make_deck(name="keep")
    gone = make_deck(name="gone")

    db.delete_deck(gone.id)

    assert db.list_all_decks() == [keep]


def test_delete_missing_raises(db):
    with pytest.raises(NotFoundError):
        db.delete_deck(1)


def test_delete_keeps_exam(make_exam, make_deck, db):
    exam = make_exam()
    deck = make_deck(exam_id=exam.id)

    db.delete_deck(deck.id)

    assert db.get_exam(exam.id) == exam


def test_delete_cascades_to_cards_and_reviews(make_deck, make_card, db):
    deck = make_deck()
    other = make_deck()
    card = make_card(deck.id)
    other_card = make_card(other.id)
    for c in (card, other_card):
        db.save_review(c.id, db.get_card(c.id), ReviewLogCreate(rating=Rating.GOOD, reviewed_at=NOW))

    db.delete_deck(deck.id)

    with pytest.raises(NotFoundError):
        db.get_card(card.id)
    assert [c.id for c in db.list_cards(other.id)] == [other_card.id]
    with db._session() as session:
        assert [log.card_id for log in session.query(ReviewLog)] == [other_card.id]
