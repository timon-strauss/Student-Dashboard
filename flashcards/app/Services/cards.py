from datetime import datetime, timezone

from Database import db
from Database import schemas as db_schemas
from Routers.schemas import CardCreate, CardResponse, CardUpdate
from schemas import Rating

from . import scheduler
from ._errors import translate_errors


def _to_response(card: db_schemas.CardResponse) -> CardResponse:
    return CardResponse.model_validate(card.model_dump())


@translate_errors
def list_cards_by_deck(deck_id: int, due: bool = False) -> list[CardResponse]:
    cards = db.list_due_cards_by_deck(deck_id) if due else db.list_cards(deck_id)
    return [_to_response(card) for card in cards]


@translate_errors
def list_cards_by_exam(exam_id: int, due: bool = False) -> list[CardResponse]:
    cards = db.list_due_cards_by_exam(exam_id) if due else db.list_cards_by_exam(exam_id)
    return [_to_response(card) for card in cards]


@translate_errors
def get_card(card_id: int) -> CardResponse:
    return _to_response(db.get_card(card_id))


@translate_errors
def create_card(data: CardCreate) -> CardResponse:
    return _to_response(db.create_card(db_schemas.CardCreate(**data.model_dump())))


@translate_errors
def update_card(card_id: int, data: CardUpdate) -> CardResponse:
    changes = db_schemas.CardUpdate(**data.model_dump(exclude_unset=True))
    return _to_response(db.update_card(card_id, changes))


@translate_errors
def reposition_card(card_id: int, position: int) -> CardResponse:
    return _to_response(db.reposition_card(card_id, position))


@translate_errors
def review_card(card_id: int, rating: Rating) -> CardResponse:
    reviewed_at = datetime.now(timezone.utc)
    schedule = scheduler.review(card_id, db.get_card(card_id), rating, reviewed_at)
    review = db_schemas.ReviewLogCreate(rating=rating, reviewed_at=reviewed_at)
    return _to_response(db.save_review(card_id, schedule, review))


@translate_errors
def delete_card(card_id: int) -> None:
    db.delete_card(card_id)
