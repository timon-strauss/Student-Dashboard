from app.Database import db
from app.Database import schemas as db_schemas
from app.Routers.schemas import YearCreate, YearResponse, YearUpdate

from ._errors import translate_errors


def _to_response(year: db_schemas.YearResponse) -> YearResponse:
    return YearResponse.model_validate(year.model_dump())


@translate_errors
def list_years() -> list[YearResponse]:
    return [_to_response(year) for year in db.list_years()]


@translate_errors
def get_year(year_id: int) -> YearResponse:
    return _to_response(db.get_year(year_id))


@translate_errors
def create_year(data: YearCreate) -> YearResponse:
    return _to_response(db.create_year(db_schemas.YearCreate(**data.model_dump())))


@translate_errors
def update_year(year_id: int, data: YearUpdate) -> YearResponse:
    changes = db_schemas.YearUpdate(**data.model_dump(exclude_unset=True))
    return _to_response(db.update_year(year_id, changes))


@translate_errors
def reposition_year(year_id: int, position: int) -> YearResponse:
    return _to_response(db.reposition_year(year_id, position))


@translate_errors
def delete_year(year_id: int) -> None:
    db.delete_year(year_id)
