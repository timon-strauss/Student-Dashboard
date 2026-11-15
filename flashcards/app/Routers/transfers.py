from fastapi import APIRouter, Query, status

from ._stub import not_implemented
from .schemas import DeckResponse, DeckTransfer, ExamResponse, ExamTransfer

router = APIRouter(prefix="/transfer", tags=["transfer"])


@router.get("/exams/{exam_id}", response_model=ExamTransfer)
def export_exam(exam_id: int) -> ExamTransfer:
    not_implemented()


@router.get("/decks/{deck_id}", response_model=DeckTransfer)
def export_deck(deck_id: int) -> DeckTransfer:
    not_implemented()


@router.post("/exams", response_model=ExamResponse, status_code=status.HTTP_201_CREATED)
def import_exam(data: ExamTransfer) -> ExamResponse:
    not_implemented()


@router.post("/decks", response_model=DeckResponse, status_code=status.HTTP_201_CREATED)
def import_deck(
    data: DeckTransfer,
    exam_id: int | None = Query(default=None, description="Exam to add the deck to; omitted imports it without an exam"),
) -> DeckResponse:
    not_implemented()
