from datetime import timedelta, timezone

import fsrs
import pytest

from Database import NotFoundError
from Database.models import ReviewLog
from Database.schemas import (
    CardSchedule,
    CardState,
    Rating,
    ReviewLogCreate,
    ReviewLogResponse,
)

from .conftest import NOW


def review_schedule(**overrides):
    values = dict(
        state=CardState.REVIEW,
        step=None,
        stability=3.5,
        difficulty=6.2,
        due=NOW + timedelta(days=4),
        last_review=NOW,
    )
    values.update(overrides)
    return CardSchedule(**values)


def test_save_review_updates_schedule(make_deck, make_card, db):
    card = make_card(make_deck().id, front="f", position=4)
    schedule = review_schedule()

    updated = db.save_review(card.id, schedule, ReviewLogCreate(rating=Rating.EASY, reviewed_at=NOW))

    assert updated.model_dump(include=set(CardSchedule.model_fields)) == schedule.model_dump()
    assert (updated.front, updated.position, updated.deck_id) == ("f", 4, card.deck_id)
    assert db.get_card(card.id) == updated


def test_save_review_writes_log(make_deck, make_card, db):
    card = make_card(make_deck().id)

    db.save_review(card.id, review_schedule(), ReviewLogCreate(rating=Rating.HARD, reviewed_at=NOW))

    logs = db.list_review_logs(card.id)
    assert len(logs) == 1
    assert isinstance(logs[0], ReviewLogResponse)
    assert (logs[0].card_id, logs[0].rating, logs[0].reviewed_at) == (card.id, Rating.HARD, NOW)


def test_save_review_normalizes_timezones(make_deck, make_card, db):
    card = make_card(make_deck().id)
    tz = timezone(timedelta(hours=-7))
    schedule = review_schedule(due=(NOW + timedelta(days=1)).astimezone(tz), last_review=NOW.astimezone(tz))

    updated = db.save_review(card.id, schedule, ReviewLogCreate(rating=3, reviewed_at=NOW.astimezone(tz)))

    assert updated.due == NOW + timedelta(days=1)
    assert updated.due.utcoffset() == timedelta(0)
    assert db.list_review_logs(card.id)[0].reviewed_at.utcoffset() == timedelta(0)


def test_reviewed_card_leaves_due_list(make_deck, make_card, db):
    deck = make_deck()
    card = make_card(deck.id)
    assert [c.id for c in db.list_due_cards_by_deck(deck.id, now=NOW + timedelta(seconds=1))] == []

    db.save_review(card.id, review_schedule(), ReviewLogCreate(rating=3, reviewed_at=NOW))

    assert db.list_due_cards_by_deck(deck.id, now=NOW + timedelta(days=1)) == []
    assert [c.id for c in db.list_due_cards_by_deck(deck.id, now=NOW + timedelta(days=4))] == [card.id]


def test_save_review_missing_card_raises_and_writes_nothing(db):
    with pytest.raises(NotFoundError) as exc:
        db.save_review(1, review_schedule(), ReviewLogCreate(rating=3, reviewed_at=NOW))

    assert exc.value.entity == "Card"
    with db._session() as session:
        assert session.query(ReviewLog).count() == 0


def test_list_review_logs_ordered_by_time(make_deck, make_card, db):
    card = make_card(make_deck().id)
    times = [NOW + timedelta(days=2), NOW, NOW + timedelta(days=1)]
    for i, reviewed_at in enumerate(times):
        db.save_review(card.id, review_schedule(), ReviewLogCreate(rating=i + 1, reviewed_at=reviewed_at))

    logs = db.list_review_logs(card.id)

    assert [log.reviewed_at for log in logs] == sorted(times)
    assert [log.rating for log in logs] == [Rating.HARD, Rating.GOOD, Rating.AGAIN]


def test_list_review_logs_only_for_card(make_deck, make_card, db):
    deck = make_deck()
    card = make_card(deck.id)
    other = make_card(deck.id)
    db.save_review(other.id, review_schedule(), ReviewLogCreate(rating=3, reviewed_at=NOW))

    assert db.list_review_logs(card.id) == []


def test_list_review_logs_missing_card_raises(db):
    with pytest.raises(NotFoundError):
        db.list_review_logs(1)


def test_delete_card_removes_logs(make_deck, make_card, db):
    card = make_card(make_deck().id)
    db.save_review(card.id, review_schedule(), ReviewLogCreate(rating=3, reviewed_at=NOW))

    db.delete_card(card.id)

    with db._session() as session:
        assert session.query(ReviewLog).count() == 0


def to_fsrs(card):
    return fsrs.Card(
        card_id=card.id,
        state=fsrs.State(card.state),
        step=card.step,
        stability=card.stability,
        difficulty=card.difficulty,
        due=card.due,
        last_review=card.last_review,
    )


def test_fsrs_roundtrip_over_multiple_reviews(make_deck, make_card, db):
    scheduler = fsrs.Scheduler(enable_fuzzing=False)
    card = make_card(make_deck().id)
    reviewed_at = NOW

    for rating in (fsrs.Rating.Good, fsrs.Rating.Good, fsrs.Rating.Again, fsrs.Rating.Easy):
        scheduled, _ = scheduler.review_card(to_fsrs(card), rating, reviewed_at)
        card = db.save_review(
            card.id,
            CardSchedule.model_validate(scheduled),
            ReviewLogCreate(rating=int(rating), reviewed_at=reviewed_at),
        )
        stored = db.get_card(card.id)

        assert stored.state == scheduled.state.value
        assert stored.step == scheduled.step
        assert stored.stability == pytest.approx(scheduled.stability)
        assert stored.difficulty == pytest.approx(scheduled.difficulty)
        assert stored.due == scheduled.due
        assert stored.last_review == scheduled.last_review
        reviewed_at = stored.due

    assert [log.rating for log in db.list_review_logs(card.id)] == [3, 3, 1, 4]
