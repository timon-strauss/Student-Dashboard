from fastapi import APIRouter

from ._stub import not_implemented
from .schemas import CardStatusCounts, ConsolidatedPoint, DueCount

router = APIRouter(prefix="/statistics", tags=["statistics"])


@router.get("/due", response_model=DueCount)
def get_due_count() -> DueCount:
    not_implemented()


@router.get("/exams/{exam_id}", response_model=CardStatusCounts)
def get_exam_status_counts(exam_id: int) -> CardStatusCounts:
    not_implemented()


@router.get("/decks/{deck_id}", response_model=CardStatusCounts)
def get_deck_status_counts(deck_id: int) -> CardStatusCounts:
    not_implemented()


@router.get(
    "/exams/{exam_id}/consolidated-history",
    response_model=list[ConsolidatedPoint],
    description="One point per day from the first card's creation until the exam date",
)
def get_exam_consolidated_history(exam_id: int) -> list[ConsolidatedPoint]:
    not_implemented()
