from fastapi import APIRouter, HTTPException, Query, status

from Services import cards as card_service

from .schemas import CardCreate, CardReposition, CardResponse, CardReview, CardUpdate

router = APIRouter(prefix="/cards", tags=["cards"])


@router.get("", response_model=list[CardResponse])
def list_cards(
    deck_id: int | None = Query(default=None, description="Cards of this deck"),
    exam_id: int | None = Query(default=None, description="Cards of all decks of this exam"),
    due: bool = Query(default=False, description="Only due cards, ordered by due date instead of position"),
) -> list[CardResponse]:
    if deck_id is not None and exam_id is None:
        return card_service.list_cards_by_deck(deck_id, due)
    if exam_id is not None and deck_id is None:
        return card_service.list_cards_by_exam(exam_id, due)
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail="Exactly one of deck_id or exam_id is required",
    )


@router.post("", response_model=CardResponse, status_code=status.HTTP_201_CREATED)
def create_card(data: CardCreate) -> CardResponse:
    return card_service.create_card(data)


@router.get("/{card_id}", response_model=CardResponse)
def get_card(card_id: int) -> CardResponse:
    return card_service.get_card(card_id)


@router.patch("/{card_id}", response_model=CardResponse)
def update_card(card_id: int, data: CardUpdate) -> CardResponse:
    return card_service.update_card(card_id, data)


@router.put("/{card_id}/position", response_model=CardResponse)
def reposition_card(card_id: int, data: CardReposition) -> CardResponse:
    return card_service.reposition_card(card_id, data.position)


@router.post("/{card_id}/review", response_model=CardResponse)
def review_card(card_id: int, data: CardReview) -> CardResponse:
    return card_service.review_card(card_id, data.rating)


@router.delete("/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_card(card_id: int) -> None:
    card_service.delete_card(card_id)
