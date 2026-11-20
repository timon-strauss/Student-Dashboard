from app.Database import db
from app.Database import schemas as db_schemas
from app.Routers.schemas import ExamCreate, ExamResponse, ExamUpdate

from ._errors import translate_errors


def _to_response(exam: db_schemas.ExamResponse) -> ExamResponse:
    return ExamResponse.model_validate(exam.model_dump())


@translate_errors
def list_exams() -> list[ExamResponse]:
    return [_to_response(exam) for exam in db.list_exams()]


@translate_errors
def get_exam(exam_id: int) -> ExamResponse:
    return _to_response(db.get_exam(exam_id))


@translate_errors
def create_exam(data: ExamCreate) -> ExamResponse:
    return _to_response(db.create_exam(db_schemas.ExamCreate(**data.model_dump())))


@translate_errors
def update_exam(exam_id: int, data: ExamUpdate) -> ExamResponse:
    changes = db_schemas.ExamUpdate(**data.model_dump(exclude_unset=True))
    return _to_response(db.update_exam(exam_id, changes))


@translate_errors
def delete_exam(exam_id: int) -> None:
    db.delete_exam(exam_id)
