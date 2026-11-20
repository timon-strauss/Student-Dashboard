from datetime import datetime, timedelta, timezone

import pytest

from app.Database import db
from app.Database.schemas import CardSchedule
from app.schemas import CardState, Rating
from app.Services import NotFoundError, cards, scheduler

NOW = datetime(2026, 6, 1, 12, 0, tzinfo=timezone.utc)
NEW_CARD = CardSchedule(state=CardState.LEARNING, step=0, stability=None, difficulty=None, due=NOW, last_review=None)


def test_new_card_good_moves_to_next_learning_step():
    schedule = scheduler.review(1, NEW_CARD, Rating.GOOD, NOW)
    assert schedule.state == CardState.LEARNING
    assert schedule.step == 1
    assert schedule.stability is not None
    assert schedule.difficulty is not None
    assert schedule.last_review == NOW
    assert schedule.due == NOW + timedelta(minutes=10)


def test_new_card_easy_graduates_to_review():
    schedule = scheduler.review(1, NEW_CARD, Rating.EASY, NOW)
    assert schedule.state == CardState.REVIEW
    assert schedule.step is None
    assert schedule.due >= NOW + timedelta(days=1)


def test_review_card_lapse_goes_to_relearning():
    graduated = scheduler.review(1, NEW_CARD, Rating.EASY, NOW)
    lapsed = scheduler.review(1, graduated, Rating.AGAIN, graduated.due)
    assert lapsed.state == CardState.RELEARNING
    assert lapsed.step == 0


def test_review_card_saves_schedule_and_log(make_deck, make_card):
    card = make_card(make_deck().id)
    reviewed = cards.review_card(card.id, Rating.GOOD)
    assert reviewed.state == CardState.LEARNING
    assert reviewed.last_review is not None
    assert reviewed.due > reviewed.last_review
    assert cards.get_card(card.id) == reviewed

    logs = db.list_review_logs(card.id)
    assert len(logs) == 1
    assert logs[0].rating == Rating.GOOD
    assert logs[0].reviewed_at == reviewed.last_review


def test_reviewed_card_is_no_longer_due(make_deck, make_card):
    deck = make_deck()
    card = make_card(deck.id)
    cards.review_card(card.id, Rating.EASY)
    assert cards.list_cards_by_deck(deck.id, due=True) == []


def test_review_unknown_card(started):
    with pytest.raises(NotFoundError) as error:
        cards.review_card(42, Rating.GOOD)
    assert error.value.entity == "Card"


def test_review_endpoint(client):
    deck = client.post("/api/decks", json={"name": "Deck"}).json()
    card = client.post("/api/cards", json={"deck_id": deck["id"], "front": "A", "back": "a"}).json()

    response = client.post(f"/api/cards/{card['id']}/review", json={"rating": 3})
    assert response.status_code == 200
    assert response.json()["last_review"] is not None

    assert client.post(f"/api/cards/{card['id']}/review", json={"rating": 5}).status_code == 422
    assert client.post("/api/cards/999/review", json={"rating": 3}).status_code == 404
