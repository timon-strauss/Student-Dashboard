from fastapi import APIRouter

from app.Services import statistics as statistics_service

from .schemas import CardStatusCounts, ConsolidatedPoint, DueCount

router = APIRouter(prefix="/statistics", tags=["statistics"])


@router.get("/due", response_model=DueCount)
def get_due_count() -> DueCount:
    return statistics_service.get_due_count()


@router.get("/exams/{exam_id}", response_model=CardStatusCounts)
def get_exam_status_counts(exam_id: int) -> CardStatusCounts:
    return statistics_service.get_exam_status_counts(exam_id)


@router.get("/decks/{deck_id}", response_model=CardStatusCounts)
def get_deck_status_counts(deck_id: int) -> CardStatusCounts:
    return statistics_service.get_deck_status_counts(deck_id)


@router.get(
    "/exams/{exam_id}/consolidated-history",
    response_model=list[ConsolidatedPoint],
    description="One point per day from the first card's creation until the exam date",
)
def get_exam_consolidated_history(exam_id: int) -> list[ConsolidatedPoint]:
    return statistics_service.get_exam_consolidated_history(exam_id)
