from app.Database import db
from app.Database import schemas as db_schemas
from app.Routers.schemas import SubmoduleCreate, SubmoduleResponse, SubmoduleUpdate

from ._errors import translate_errors
from ._grading import check_submodule_allowed, require_supported_max_points, submodule_grade


def _to_response(submodule: db_schemas.SubmoduleResponse) -> SubmoduleResponse:
    return SubmoduleResponse(**submodule.model_dump(), grade=submodule_grade(submodule))


@translate_errors
def list_submodules(module_id: int) -> list[SubmoduleResponse]:
    return [_to_response(submodule) for submodule in db.list_submodules(module_id)]


@translate_errors
def get_submodule(submodule_id: int) -> SubmoduleResponse:
    return _to_response(db.get_submodule(submodule_id))


@translate_errors
def create_submodule(data: SubmoduleCreate) -> SubmoduleResponse:
    check_submodule_allowed(db.get_module(data.module_id))
    require_supported_max_points(data.max_points)
    return _to_response(db.create_submodule(db_schemas.SubmoduleCreate(**data.model_dump())))


@translate_errors
def update_submodule(submodule_id: int, data: SubmoduleUpdate) -> SubmoduleResponse:
    changes = data.model_dump(exclude_unset=True)
    if "max_points" in changes:
        require_supported_max_points(changes["max_points"])
    return _to_response(db.update_submodule(submodule_id, db_schemas.SubmoduleUpdate(**changes)))


@translate_errors
def delete_submodule(submodule_id: int) -> None:
    db.delete_submodule(submodule_id)
