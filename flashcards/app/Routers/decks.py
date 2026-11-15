from fastapi import APIRouter, Query, status

from Services import decks as deck_service

from .schemas import DeckCreate, DeckResponse, DeckUpdate

router = APIRouter(prefix="/decks", tags=["decks"])


@router.get("", response_model=list[DeckResponse])
def list_decks(
    exam_id: int | None = Query(
        default=None,
        description="Decks of this exam; omitted returns decks without an exam",
    ),
) -> list[DeckResponse]:
    return deck_service.list_decks(exam_id)


@router.post("", response_model=DeckResponse, status_code=status.HTTP_201_CREATED)
def create_deck(data: DeckCreate) -> DeckResponse:
    return deck_service.create_deck(data)


@router.get("/{deck_id}", response_model=DeckResponse)
def get_deck(deck_id: int) -> DeckResponse:
    return deck_service.get_deck(deck_id)


@router.patch("/{deck_id}", response_model=DeckResponse)
def update_deck(deck_id: int, data: DeckUpdate) -> DeckResponse:
    return deck_service.update_deck(deck_id, data)


@router.delete("/{deck_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_deck(deck_id: int) -> None:
    deck_service.delete_deck(deck_id)
