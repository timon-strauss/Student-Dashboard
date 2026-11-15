from datetime import datetime

from fsrs import Card as FsrsCard
from fsrs import Rating as FsrsRating
from fsrs import Scheduler
from fsrs import State as FsrsState

from Database.schemas import CardSchedule
from schemas import CardState, Rating

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
