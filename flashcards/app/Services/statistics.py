from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone

from app.Database import db
from app.Database import schemas as db_schemas
from app.Routers.schemas import CardStatusCounts, ConsolidatedPoint, DueCount
from app.schemas import Rating

from . import scheduler
from ._errors import translate_errors


def _utc_date(value: datetime) -> date:
    return value.astimezone(timezone.utc).date()


def _status_counts(
    cards: list[db_schemas.CardResponse], exam_date: datetime | None, now: datetime
) -> CardStatusCounts:
    due = learned = consolidated = 0
    for card in cards:
        if scheduler.is_due(card, now):
            due += 1
        elif scheduler.is_consolidated(card, exam_date):
            consolidated += 1
        else:
            learned += 1
    return CardStatusCounts(due=due, learned=learned, consolidated=consolidated)


@translate_errors
def get_due_count() -> DueCount:
    return DueCount(due=len(db.list_due_cards(datetime.now(timezone.utc))))


@translate_errors
def get_exam_status_counts(exam_id: int) -> CardStatusCounts:
    exam = db.get_exam(exam_id)
    return _status_counts(db.list_cards_by_exam(exam_id), exam.exam_date, datetime.now(timezone.utc))


@translate_errors
def get_deck_status_counts(deck_id: int) -> CardStatusCounts:
    deck = db.get_deck(deck_id)
    exam_date = db.get_exam(deck.exam_id).exam_date if deck.exam_id is not None else None
    return _status_counts(db.list_cards(deck_id), exam_date, datetime.now(timezone.utc))


@translate_errors
def get_exam_consolidated_history(exam_id: int) -> list[ConsolidatedPoint]:
    exam = db.get_exam(exam_id)
    cards = db.list_cards_by_exam(exam_id)
    if not cards:
        return []

    reviews: dict[int, list[tuple[Rating, datetime]]] = defaultdict(list)
    for log in db.list_review_logs_by_exam(exam_id):
        reviews[log.card_id].append((log.rating, log.reviewed_at))

    changes: Counter[date] = Counter()
    for card in cards:
        consolidated = False
        for reviewed_at, schedule in scheduler.replay(card.id, card.created_at, reviews[card.id]):
            now_consolidated = scheduler.is_consolidated(schedule, exam.exam_date)
            if now_consolidated != consolidated:
                changes[_utc_date(reviewed_at)] += 1 if now_consolidated else -1
                consolidated = now_consolidated

    start = min(_utc_date(card.created_at) for card in cards)
    end = _utc_date(exam.exam_date)
    history = []
    count = 0
    day = start
    while day <= end:
        count += changes[day]
        history.append(ConsolidatedPoint(date=day, consolidated=count))
        day += timedelta(days=1)
    return history
