from app.Database import db
from app.Database import schemas as db_schemas
from app.Routers.schemas import SubmoduleCreate, SubmoduleResponse, SubmoduleUpdate

from ._errors import translate_errors
from ._grading import check_submodule_allowed


def _to_response(submodule: db_schemas.SubmoduleResponse) -> SubmoduleResponse:
    return SubmoduleResponse.model_validate(submodule.model_dump())


@translate_errors
def list_submodules(module_id: int | None) -> list[SubmoduleResponse]:
    submodules = db.list_all_submodules() if module_id is None else db.list_submodules(module_id)
    return [_to_response(submodule) for submodule in submodules]


@translate_errors
def get_submodule(submodule_id: int) -> SubmoduleResponse:
    return _to_response(db.get_submodule(submodule_id))


@translate_errors
def create_submodule(data: SubmoduleCreate) -> SubmoduleResponse:
    check_submodule_allowed(db.get_module(data.module_id))
    return _to_response(db.create_submodule(db_schemas.SubmoduleCreate(**data.model_dump())))


@translate_errors
def update_submodule(submodule_id: int, data: SubmoduleUpdate) -> SubmoduleResponse:
    changes = data.model_dump(exclude_unset=True)
    return _to_response(db.update_submodule(submodule_id, db_schemas.SubmoduleUpdate(**changes)))


@translate_errors
def delete_submodule(submodule_id: int) -> None:
    db.delete_submodule(submodule_id)
