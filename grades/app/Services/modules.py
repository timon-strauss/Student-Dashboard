from app.Database import db
from app.Database import schemas as db_schemas
from app.Routers.schemas import ModuleCreate, ModuleResponse, ModuleUpdate

from ._errors import translate_errors
from ._grading import check_module_state, resolve, submodules_by_module


def _to_response(
    module: db_schemas.ModuleResponse, submodules: list[db_schemas.SubmoduleResponse]
) -> ModuleResponse:
    result = resolve(module, submodules)
    return ModuleResponse(
        id=module.id,
        year_id=module.year_id,
        name=module.name,
        ects=module.ects,
        grade=result.grade,
        passed=result.passed,
        grade_from_submodules=result.grade_from_submodules,
    )


@translate_errors
def list_modules(year_id: int | None) -> list[ModuleResponse]:
    modules = db.list_all_modules() if year_id is None else db.list_modules(year_id)
    submodules = submodules_by_module()
    return [_to_response(module, submodules[module.id]) for module in modules]


@translate_errors
def get_module(module_id: int) -> ModuleResponse:
    return _to_response(db.get_module(module_id), db.list_submodules(module_id))


@translate_errors
def create_module(data: ModuleCreate) -> ModuleResponse:
    check_module_state(data.grade, data.passed, has_submodules=False)
    return _to_response(db.create_module(db_schemas.ModuleCreate(**data.model_dump())), [])


@translate_errors
def update_module(module_id: int, data: ModuleUpdate) -> ModuleResponse:
    current = db.get_module(module_id)
    submodules = db.list_submodules(module_id)
    changes = data.model_dump(exclude_unset=True)
    check_module_state(
        changes.get("grade", current.grade),
        changes.get("passed", current.passed),
        has_submodules=bool(submodules),
    )
    updated = db.update_module(module_id, db_schemas.ModuleUpdate(**changes))
    return _to_response(updated, submodules)


@translate_errors
def delete_module(module_id: int) -> None:
    db.delete_module(module_id)
