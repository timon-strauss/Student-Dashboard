from fastapi import APIRouter, Query, status

from ._stub import not_implemented
from .schemas import CardCreate, CardReposition, CardResponse, CardReview, CardUpdate

router = APIRouter(prefix="/cards", tags=["cards"])


@router.get("", response_model=list[CardResponse])
def list_cards(deck_id: int = Query(description="Cards of this deck, ordered by position")) -> list[CardResponse]:
    not_implemented()


@router.get("/due/exams/{exam_id}", response_model=list[CardResponse])
def list_due_cards_by_exam(exam_id: int) -> list[CardResponse]:
    not_implemented()


@router.get("/due/decks/{deck_id}", response_model=list[CardResponse])
def list_due_cards_by_deck(deck_id: int) -> list[CardResponse]:
    not_implemented()


@router.post("", response_model=CardResponse, status_code=status.HTTP_201_CREATED)
def create_card(data: CardCreate) -> CardResponse:
    not_implemented()


@router.get("/{card_id}", response_model=CardResponse)
def get_card(card_id: int) -> CardResponse:
    not_implemented()


@router.patch("/{card_id}", response_model=CardResponse)
def update_card(card_id: int, data: CardUpdate) -> CardResponse:
    not_implemented()


@router.put("/{card_id}/position", response_model=CardResponse)
def reposition_card(card_id: int, data: CardReposition) -> CardResponse:
    not_implemented()


@router.post("/{card_id}/review", response_model=CardResponse)
def review_card(card_id: int, data: CardReview) -> CardResponse:
    not_implemented()


@router.delete("/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_card(card_id: int) -> None:
    not_implemented()
