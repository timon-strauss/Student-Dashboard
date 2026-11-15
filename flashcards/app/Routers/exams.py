from fastapi import APIRouter, status

from ._stub import not_implemented
from .schemas import ExamCreate, ExamResponse, ExamUpdate

router = APIRouter(prefix="/exams", tags=["exams"])


@router.get("", response_model=list[ExamResponse])
def list_exams() -> list[ExamResponse]:
    not_implemented()


@router.post("", response_model=ExamResponse, status_code=status.HTTP_201_CREATED)
def create_exam(data: ExamCreate) -> ExamResponse:
    not_implemented()


@router.get("/{exam_id}", response_model=ExamResponse)
def get_exam(exam_id: int) -> ExamResponse:
    not_implemented()


@router.patch("/{exam_id}", response_model=ExamResponse)
def update_exam(exam_id: int, data: ExamUpdate) -> ExamResponse:
    not_implemented()


@router.delete("/{exam_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_exam(exam_id: int) -> None:
    not_implemented()
