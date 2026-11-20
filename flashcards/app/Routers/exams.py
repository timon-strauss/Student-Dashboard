from fastapi import APIRouter, status

from app.Services import exams as exam_service

from .schemas import ExamCreate, ExamResponse, ExamUpdate

router = APIRouter(prefix="/exams", tags=["exams"])


@router.get("", response_model=list[ExamResponse])
def list_exams() -> list[ExamResponse]:
    return exam_service.list_exams()


@router.post("", response_model=ExamResponse, status_code=status.HTTP_201_CREATED)
def create_exam(data: ExamCreate) -> ExamResponse:
    return exam_service.create_exam(data)


@router.get("/{exam_id}", response_model=ExamResponse)
def get_exam(exam_id: int) -> ExamResponse:
    return exam_service.get_exam(exam_id)


@router.patch("/{exam_id}", response_model=ExamResponse)
def update_exam(exam_id: int, data: ExamUpdate) -> ExamResponse:
    return exam_service.update_exam(exam_id, data)


@router.delete("/{exam_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_exam(exam_id: int) -> None:
    exam_service.delete_exam(exam_id)
