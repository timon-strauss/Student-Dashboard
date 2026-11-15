from fastapi import APIRouter, Query, status

from ._stub import not_implemented
from .schemas import DeckCreate, DeckResponse, DeckUpdate

router = APIRouter(prefix="/decks", tags=["decks"])


@router.get("", response_model=list[DeckResponse])
def list_decks(
    exam_id: int | None = Query(
        default=None,
        description="Decks of this exam; omitted returns decks without an exam",
    ),
) -> list[DeckResponse]:
    not_implemented()


@router.post("", response_model=DeckResponse, status_code=status.HTTP_201_CREATED)
def create_deck(data: DeckCreate) -> DeckResponse:
    not_implemented()


@router.get("/{deck_id}", response_model=DeckResponse)
def get_deck(deck_id: int) -> DeckResponse:
    not_implemented()


@router.patch("/{deck_id}", response_model=DeckResponse)
def update_deck(deck_id: int, data: DeckUpdate) -> DeckResponse:
    not_implemented()


@router.delete("/{deck_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_deck(deck_id: int) -> None:
    not_implemented()
