from datetime import datetime, timedelta, timezone

import pytest

from Database import NotFoundError
from Database.schemas import CardCreate, CardResponse, CardState, CardUpdate

from .conftest import NOW


class TestCreateAndGet:
    def test_create_new_card_has_initial_schedule(self, make_deck, db):
        before = datetime.now(timezone.utc)
        deck = make_deck()

        card = db.create_card(
            CardCreate(
                deck_id=deck.id,
                front="Was ist 2+2?",
                back="4",
                front_image="f.png",
                back_image="b.png",
                position=3,
            )
        )

        assert isinstance(card, CardResponse)
        assert (card.front, card.back, card.front_image, card.back_image, card.position) == (
            "Was ist 2+2?",
            "4",
            "f.png",
            "b.png",
            3,
        )
        assert card.state is CardState.LEARNING
        assert card.step == 0
        assert card.stability is None
        assert card.difficulty is None
        assert card.last_review is None
        assert card.due.tzinfo is not None
        assert before - timedelta(seconds=1) <= card.due <= datetime.now(timezone.utc)
        assert before - timedelta(seconds=1) <= card.created_at <= datetime.now(timezone.utc)
        assert card.created_at.utcoffset() == timedelta(0)

    def test_get_returns_created_card(self, make_deck, make_card, db):
        card = make_card(make_deck().id)

        assert db.get_card(card.id) == card

    def test_create_missing_deck_raises(self, db):
        with pytest.raises(NotFoundError) as exc:
            db.create_card(CardCreate(deck_id=7, front="f", back="b"))

        assert (exc.value.entity, exc.value.entity_id) == ("Deck", 7)

    def test_get_missing_raises(self, db):
        with pytest.raises(NotFoundError) as exc:
            db.get_card(1)

        assert exc.value.entity == "Card"


class TestListCards:
    def test_ordered_by_position(self, make_deck, make_card, db):
        deck = make_deck()
        c2 = make_card(deck.id, position=2)
        c0 = make_card(deck.id, position=0)
        c1 = make_card(deck.id, position=1)

        assert [c.id for c in db.list_cards(deck.id)] == [c0.id, c1.id, c2.id]

    def test_only_cards_of_deck(self, make_deck, make_card, db):
        deck = make_deck()
        other = make_deck()
        card = make_card(deck.id)
        make_card(other.id)

        assert db.list_cards(deck.id) == [card]

    def test_empty_deck(self, make_deck, db):
        assert db.list_cards(make_deck().id) == []

    def test_missing_deck_raises(self, db):
        with pytest.raises(NotFoundError):
            db.list_cards(1)


class TestDueCards:
    @pytest.fixture
    def setup(self, make_exam, make_deck, make_card, set_due):
        exam = make_exam()
        other_exam = make_exam(name="other")
        deck = make_deck(exam_id=exam.id)
        deck2 = make_deck(exam_id=exam.id)
        other_deck = make_deck(exam_id=other_exam.id)
        free_deck = make_deck(exam_id=None)

        def card(deck_id, due):
            c = make_card(deck_id)
            set_due(c.id, due)
            return c.id

        return {
            "exam": exam.id,
            "deck": deck.id,
            "deck2": deck2.id,
            "old": card(deck.id, NOW - timedelta(days=3)),
            "recent": card(deck2.id, NOW - timedelta(hours=1)),
            "exact": card(deck.id, NOW),
            "future": card(deck.id, NOW + timedelta(seconds=1)),
            "other": card(other_deck.id, NOW - timedelta(days=2)),
            "free": card(free_deck.id, NOW - timedelta(days=1)),
        }

    def test_all_due_cards_ordered_by_due(self, setup, db):
        ids = [c.id for c in db.list_due_cards(now=NOW)]

        assert ids == [
            setup["old"],
            setup["other"],
            setup["free"],
            setup["recent"],
            setup["exact"],
        ]

    def test_due_respects_now_timezone(self, setup, db):
        local_now = (NOW - timedelta(hours=2)).astimezone(timezone(timedelta(hours=5)))

        ids = {c.id for c in db.list_due_cards(now=local_now)}

        assert ids == {setup["old"], setup["other"], setup["free"]}

    def test_due_defaults_to_current_time(self, make_deck, make_card, set_due, db):
        deck = make_deck()
        due_now = make_card(deck.id)
        later = make_card(deck.id)
        set_due(later.id, datetime.now(timezone.utc) + timedelta(days=1))

        assert [c.id for c in db.list_due_cards()] == [due_now.id]

    def test_nothing_due(self, setup, db):
        assert db.list_due_cards(now=NOW - timedelta(days=10)) == []

    def test_by_exam_includes_all_decks_of_exam(self, setup, db):
        ids = [c.id for c in db.list_due_cards_by_exam(setup["exam"], now=NOW)]

        assert ids == [setup["old"], setup["recent"], setup["exact"]]

    def test_by_exam_defaults_to_current_time(self, make_exam, make_deck, make_card, db):
        exam = make_exam()
        card = make_card(make_deck(exam_id=exam.id).id)

        assert [c.id for c in db.list_due_cards_by_exam(exam.id)] == [card.id]

    def test_by_exam_missing_raises(self, db):
        with pytest.raises(NotFoundError) as exc:
            db.list_due_cards_by_exam(99, now=NOW)

        assert exc.value.entity == "Exam"

    def test_by_deck(self, setup, db):
        ids = [c.id for c in db.list_due_cards_by_deck(setup["deck"], now=NOW)]

        assert ids == [setup["old"], setup["exact"]]

    def test_by_deck_defaults_to_current_time(self, make_deck, make_card, db):
        deck = make_deck()
        card = make_card(deck.id)

        assert [c.id for c in db.list_due_cards_by_deck(deck.id)] == [card.id]

    def test_by_deck_missing_raises(self, db):
        with pytest.raises(NotFoundError) as exc:
            db.list_due_cards_by_deck(99, now=NOW)

        assert exc.value.entity == "Deck"


class TestUpdate:
    def test_partial_update(self, make_deck, make_card, db):
        card = make_card(make_deck().id, front="alt", back="b", front_image="img.png")

        updated = db.update_card(card.id, CardUpdate(front="neu"))

        assert (updated.front, updated.back, updated.front_image) == ("neu", "b", "img.png")
        assert db.get_card(card.id) == updated

    def test_update_does_not_touch_schedule(self, make_deck, make_card, db):
        card = make_card(make_deck().id)

        updated = db.update_card(card.id, CardUpdate(back="x", position=5))

        assert updated.model_dump(include=set(CardResponse.model_fields) - {"back", "position"}) == card.model_dump(
            include=set(CardResponse.model_fields) - {"back", "position"}
        )

    def test_clear_image(self, make_deck, make_card, db):
        card = make_card(make_deck().id, back_image="b.png")

        assert db.update_card(card.id, CardUpdate(back_image=None)).back_image is None

    def test_missing_card_raises(self, db):
        with pytest.raises(NotFoundError) as exc:
            db.update_card(1, CardUpdate(front="x"))

        assert exc.value.entity == "Card"


class TestDelete:
    def test_delete(self, make_deck, make_card, db):
        deck = make_deck()
        keep = make_card(deck.id)
        gone = make_card(deck.id)

        db.delete_card(gone.id)

        assert db.list_cards(deck.id) == [keep]
        with pytest.raises(NotFoundError):
            db.get_card(gone.id)

    def test_delete_keeps_deck(self, make_deck, make_card, db):
        deck = make_deck()

        db.delete_card(make_card(deck.id).id)

        assert db.get_deck(deck.id) == deck

    def test_delete_missing_raises(self, db):
        with pytest.raises(NotFoundError):
            db.delete_card(1)
