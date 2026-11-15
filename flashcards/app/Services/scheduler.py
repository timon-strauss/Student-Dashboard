from collections.abc import Iterable, Iterator
from datetime import datetime

from fsrs import Card as FsrsCard
from fsrs import Rating as FsrsRating
from fsrs import Scheduler
from fsrs import State as FsrsState

from Database.schemas import CardSchedule
from schemas import CardState, Rating

from . import config

_scheduler = Scheduler()


def _to_fsrs(card_id: int, schedule: CardSchedule) -> FsrsCard:
    return FsrsCard(
        card_id=card_id,
        state=FsrsState(schedule.state),
        step=schedule.step,
        stability=schedule.stability,
        difficulty=schedule.difficulty,
        due=schedule.due,
        last_review=schedule.last_review,
    )


def _from_fsrs(card: FsrsCard) -> CardSchedule:
    return CardSchedule(
        state=CardState(card.state),
        step=card.step,
        stability=card.stability,
        difficulty=card.difficulty,
        due=card.due,
        last_review=card.last_review,
    )


def review(card_id: int, schedule: CardSchedule, rating: Rating, reviewed_at: datetime) -> CardSchedule:
    card, _ = _scheduler.review_card(_to_fsrs(card_id, schedule), FsrsRating(rating), reviewed_at)
    return _from_fsrs(card)


def new_card(created_at: datetime) -> CardSchedule:
    return CardSchedule(
        state=CardState.LEARNING,
        step=0,
        stability=None,
        difficulty=None,
        due=created_at,
        last_review=None,
    )


def replay(
    card_id: int, created_at: datetime, reviews: Iterable[tuple[Rating, datetime]]
) -> Iterator[tuple[datetime, CardSchedule]]:
    schedule = new_card(created_at)
    for rating, reviewed_at in reviews:
        schedule = review(card_id, schedule, rating, reviewed_at)
        yield reviewed_at, schedule


def is_due(schedule: CardSchedule, now: datetime) -> bool:
    return schedule.due <= now


def is_consolidated(schedule: CardSchedule, exam_date: datetime | None) -> bool:
    if schedule.last_review is None or schedule.stability is None:
        return False
    if exam_date is None:
        return schedule.stability >= config.consolidated_fallback_days()
    retrievability = _scheduler.get_card_retrievability(_to_fsrs(0, schedule), exam_date)
    return retrievability >= config.consolidated_retrievability()
