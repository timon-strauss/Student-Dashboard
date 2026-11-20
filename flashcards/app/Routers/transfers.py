from fastapi import APIRouter, Query, status

from app.Services import transfers as transfer_service

from .schemas import DeckResponse, DeckTransfer, ExamResponse, ExamTransfer

router = APIRouter(prefix="/transfer", tags=["transfer"])


@router.get("/exams/{exam_id}", response_model=ExamTransfer)
def export_exam(exam_id: int) -> ExamTransfer:
    return transfer_service.export_exam(exam_id)


@router.get("/decks/{deck_id}", response_model=DeckTransfer)
def export_deck(deck_id: int) -> DeckTransfer:
    return transfer_service.export_deck(deck_id)


@router.post("/exams", response_model=ExamResponse, status_code=status.HTTP_201_CREATED)
def import_exam(data: ExamTransfer) -> ExamResponse:
    return transfer_service.import_exam(data)


@router.post("/decks", response_model=DeckResponse, status_code=status.HTTP_201_CREATED)
def import_deck(
    data: DeckTransfer,
    exam_id: int | None = Query(default=None, description="Exam to add the deck to; omitted imports it without an exam"),
) -> DeckResponse:
    return transfer_service.import_deck(data, exam_id)
