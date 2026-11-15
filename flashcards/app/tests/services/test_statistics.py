from datetime import date, datetime, timedelta, timezone

import pytest

from Database import SQLiteDatabase, db
from Database.models import Card
from Database.schemas import CardSchedule, ReviewLogCreate
from schemas import CardState, Rating
from Services import NotFoundError, cards, config, scheduler, statistics

CREATED = datetime(2026, 5, 1, 10, 0, tzinfo=timezone.utc)
EXAM_DATE = datetime(2026, 5, 31, 9, 0, tzinfo=timezone.utc)
FAR_FUTURE = datetime(2100, 1, 1, tzinfo=timezone.utc)


@pytest.fixture(autouse=True)
def default_config(monkeypatch):
    monkeypatch.delenv("CONSOLIDATED_FALLBACK_DAYS", raising=False)
    monkeypatch.delenv("CONSOLIDATED_RETRIEVABILITY", raising=False)


@pytest.fixture
def backdate():
    def _backdate(card_id, created_at):
        with SQLiteDatabase._session() as session:
            session.get(Card, card_id).created_at = created_at
            session.commit()

    return _backdate


def reviewed(stability, last_review=CREATED, state=CardState.REVIEW):
    return CardSchedule(
        state=state,
        step=None if state == CardState.REVIEW else 0,
        stability=stability,
        difficulty=5.0,
        due=FAR_FUTURE,
        last_review=last_review,
    )


def save_schedule(card_id, stability, last_review):
    schedule = reviewed(stability, last_review)
    db.save_review(card_id, schedule, ReviewLogCreate(rating=Rating.GOOD, reviewed_at=last_review))


def save_history(card_id, reviews):
    schedule = scheduler.new_card(CREATED)
    for rating, reviewed_at in reviews:
        schedule = scheduler.review(card_id, schedule, rating, reviewed_at)
        db.save_review(card_id, schedule, ReviewLogCreate(rating=rating, reviewed_at=reviewed_at))
    return schedule


def test_never_reviewed_card_is_not_consolidated():
    assert not scheduler.is_consolidated(scheduler.new_card(CREATED), EXAM_DATE)
    assert not scheduler.is_consolidated(scheduler.new_card(CREATED), None)


def test_consolidated_when_90_percent_point_is_after_exam():
    exam_date = CREATED + timedelta(days=10)
    assert scheduler.is_consolidated(reviewed(10.0), exam_date)
    assert not scheduler.is_consolidated(reviewed(9.0), exam_date)
    assert scheduler.is_consolidated(reviewed(3.0, state=CardState.RELEARNING), CREATED + timedelta(days=2))


def test_card_reviewed_shortly_before_exam_is_consolidated_with_low_stability():
    assert scheduler.is_consolidated(reviewed(5.0), CREATED + timedelta(days=4))
    assert not scheduler.is_consolidated(reviewed(5.0), None)


def test_fallback_without_exam_uses_stability_days():
    assert not scheduler.is_consolidated(reviewed(20.9), None)
    assert scheduler.is_consolidated(reviewed(21.0), None)


def test_fallback_days_from_environment(monkeypatch):
    monkeypatch.setenv("CONSOLIDATED_FALLBACK_DAYS", "40")
    assert config.consolidated_fallback_days() == 40.0
    assert not scheduler.is_consolidated(reviewed(30.0), None)
    assert scheduler.is_consolidated(reviewed(40.0), None)


@pytest.mark.parametrize("value", ["abc", "0", "-3"])
def test_invalid_fallback_days(monkeypatch, value):
    monkeypatch.setenv("CONSOLIDATED_FALLBACK_DAYS", value)
    with pytest.raises(ValueError):
        config.validate()


def test_retrievability_from_environment(monkeypatch):
    exam_date = CREATED + timedelta(days=10)
    assert not scheduler.is_consolidated(reviewed(9.0), exam_date)
    monkeypatch.setenv("CONSOLIDATED_RETRIEVABILITY", "0.85")
    assert config.consolidated_retrievability() == 0.85
    assert scheduler.is_consolidated(reviewed(9.0), exam_date)
    monkeypatch.setenv("CONSOLIDATED_RETRIEVABILITY", "0.95")
    assert not scheduler.is_consolidated(reviewed(10.0), exam_date)


@pytest.mark.parametrize("value", ["abc", "0", "1", "1.5", "-0.2"])
def test_invalid_retrievability(monkeypatch, value):
    monkeypatch.setenv("CONSOLIDATED_RETRIEVABILITY", value)
    with pytest.raises(ValueError):
        config.validate()


def test_replay_matches_live_reviews():
    reviews = [(Rating.GOOD, CREATED), (Rating.GOOD, CREATED + timedelta(minutes=10)), (Rating.EASY, CREATED + timedelta(days=3))]
    replayed = list(scheduler.replay(1, CREATED, reviews))
    assert [reviewed_at for reviewed_at, _ in replayed] == [reviewed_at for _, reviewed_at in reviews]
    assert replayed[-1][1].stability == scheduler.review(
        1, replayed[-2][1], Rating.EASY, CREATED + timedelta(days=3)
    ).stability


def test_due_count(make_deck, make_card):
    deck = make_deck()
    first = make_card(deck.id)
    make_card(deck.id)
    assert statistics.get_due_count().due == 2
    cards.review_card(first.id, Rating.EASY)
    assert statistics.get_due_count().due == 1


def test_status_counts_with_exam(make_exam, make_deck, make_card):
    now = datetime.now(timezone.utc)
    exam = make_exam(exam_date=now + timedelta(days=30))
    deck = make_deck(exam_id=exam.id)
    make_card(deck.id)
    learning = make_card(deck.id)
    cards.review_card(learning.id, Rating.GOOD)
    weak = make_card(deck.id)
    save_schedule(weak.id, stability=25.0, last_review=now)
    strong = make_card(deck.id)
    save_schedule(strong.id, stability=40.0, last_review=now)
    make_card(make_deck().id)

    expected = {"due": 1, "learned": 2, "consolidated": 1}
    assert statistics.get_deck_status_counts(deck.id).model_dump() == expected
    assert statistics.get_exam_status_counts(exam.id).model_dump() == expected


def test_status_counts_without_exam_use_fallback(monkeypatch, make_deck, make_card):
    now = datetime.now(timezone.utc)
    deck = make_deck()
    weak = make_card(deck.id)
    save_schedule(weak.id, stability=15.0, last_review=now)
    strong = make_card(deck.id)
    save_schedule(strong.id, stability=25.0, last_review=now)
    assert statistics.get_deck_status_counts(deck.id).model_dump() == {"due": 0, "learned": 1, "consolidated": 1}

    monkeypatch.setenv("CONSOLIDATED_FALLBACK_DAYS", "30")
    assert statistics.get_deck_status_counts(deck.id).model_dump() == {"due": 0, "learned": 2, "consolidated": 0}


def test_status_counts_not_found(started):
    with pytest.raises(NotFoundError):
        statistics.get_exam_status_counts(1)
    with pytest.raises(NotFoundError):
        statistics.get_deck_status_counts(1)


def test_history_without_cards(make_exam):
    assert statistics.get_exam_consolidated_history(make_exam().id) == []


def test_history_not_found(started):
    with pytest.raises(NotFoundError):
        statistics.get_exam_consolidated_history(1)


def test_history_counts_consolidation_and_lapse(make_exam, make_deck, make_card, backdate):
    exam = make_exam(exam_date=EXAM_DATE)
    deck = make_deck(exam_id=exam.id)
    card = make_card(deck.id)
    late = make_card(deck.id)
    backdate(card.id, CREATED)
    backdate(late.id, CREATED + timedelta(days=2))

    first_reviews = [(Rating.EASY, CREATED + timedelta(hours=1)), (Rating.EASY, CREATED + timedelta(days=12))]
    replayed = [schedule for _, schedule in scheduler.replay(card.id, CREATED, first_reviews)]
    assert not scheduler.is_consolidated(replayed[0], EXAM_DATE)
    assert scheduler.is_consolidated(replayed[1], EXAM_DATE)
    save_history(card.id, [*first_reviews, (Rating.AGAIN, CREATED + timedelta(days=20))])

    late_review = CREATED + timedelta(days=25)
    late_schedule = save_history(late.id, [(Rating.EASY, late_review)])
    assert late_schedule.stability < config.DEFAULT_CONSOLIDATED_FALLBACK_DAYS
    assert scheduler.is_consolidated(late_schedule, EXAM_DATE)

    history = statistics.get_exam_consolidated_history(exam.id)
    assert history[0].date == date(2026, 5, 1)
    assert history[-1].date == date(2026, 5, 31)
    assert len(history) == 31
    counts = {point.date: point.consolidated for point in history}
    assert counts[date(2026, 5, 12)] == 0
    assert counts[date(2026, 5, 13)] == 1
    assert counts[date(2026, 5, 20)] == 1
    assert counts[date(2026, 5, 21)] == 0
    assert counts[date(2026, 5, 25)] == 0
    assert counts[date(2026, 5, 26)] == 1
    assert counts[date(2026, 5, 31)] == 1


def test_statistics_endpoints(client):
    exam = client.post("/api/exams", json={"name": "Mathe", "exam_date": "2026-12-01T09:00:00+00:00"}).json()
    deck = client.post("/api/decks", json={"exam_id": exam["id"], "name": "Deck"}).json()
    client.post("/api/cards", json={"deck_id": deck["id"], "front": "A", "back": "a"})

    assert client.get("/api/statistics/due").json() == {"due": 1}
    assert client.get(f"/api/statistics/exams/{exam['id']}").json() == {"due": 1, "learned": 0, "consolidated": 0}
    assert client.get(f"/api/statistics/decks/{deck['id']}").json() == {"due": 1, "learned": 0, "consolidated": 0}
    history = client.get(f"/api/statistics/exams/{exam['id']}/consolidated-history")
    assert history.status_code == 200
    assert history.json()[-1] == {"date": "2026-12-01", "consolidated": 0}
    assert client.get("/api/statistics/exams/999").status_code == 404
