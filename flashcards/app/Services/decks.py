from Database import db
from Database import schemas as db_schemas
from Routers.schemas import DeckCreate, DeckResponse, DeckUpdate

from ._errors import translate_errors


def _to_response(deck: db_schemas.DeckResponse) -> DeckResponse:
    return DeckResponse.model_validate(deck.model_dump())


@translate_errors
def list_decks(exam_id: int | None) -> list[DeckResponse]:
    return [_to_response(deck) for deck in db.list_decks(exam_id)]


@translate_errors
def get_deck(deck_id: int) -> DeckResponse:
    return _to_response(db.get_deck(deck_id))


@translate_errors
def create_deck(data: DeckCreate) -> DeckResponse:
    return _to_response(db.create_deck(db_schemas.DeckCreate(**data.model_dump())))


@translate_errors
def update_deck(deck_id: int, data: DeckUpdate) -> DeckResponse:
    changes = db_schemas.DeckUpdate(**data.model_dump(exclude_unset=True))
    return _to_response(db.update_deck(deck_id, changes))


@translate_errors
def delete_deck(deck_id: int) -> None:
    db.delete_deck(deck_id)
