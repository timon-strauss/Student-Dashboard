from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass

from app import Grading
from app.Database import db
from app.Database import schemas as db_schemas

from .exceptions import InvalidDataError

PASSING_GRADE = 4.0


@dataclass(frozen=True)
class ModuleResult:
    grade: float | None
    passed: bool
    grade_from_submodules: bool


def require_supported_max_points(max_points: float) -> None:
    if not Grading.is_supported(max_points):
        raise InvalidDataError(f"max_points must be one of {Grading.supported_max_points()}, got {max_points:g}")


def submodule_grade(submodule: db_schemas.SubmoduleResponse) -> float | None:
    if submodule.reached_points is None:
        return None
    return Grading.grade_for(submodule.max_points, submodule.reached_points)


def module_grade(submodules: Iterable[db_schemas.SubmoduleResponse]) -> float | None:
    graded = [(s.weight, submodule_grade(s)) for s in submodules]
    if not graded or any(grade is None for _, grade in graded):
        return None
    total_weight = sum(weight for weight, _ in graded)
    return round(sum(weight * grade for weight, grade in graded) / total_weight, 2)


def resolve(
    module: db_schemas.ModuleResponse, submodules: list[db_schemas.SubmoduleResponse]
) -> ModuleResult:
    grade = module_grade(submodules) if submodules else module.grade
    passed = grade <= PASSING_GRADE if grade is not None else module.passed
    return ModuleResult(grade=grade, passed=passed, grade_from_submodules=bool(submodules))


def check_module_state(grade: float | None, passed: bool, has_submodules: bool) -> None:
    if has_submodules and grade is not None:
        raise InvalidDataError("grade is calculated from the submodules and cannot be set")
    if passed and (grade is not None or has_submodules):
        raise InvalidDataError("passed can only be set on modules without grade and submodules")


def check_submodule_allowed(module: db_schemas.ModuleResponse) -> None:
    if module.grade is not None:
        raise InvalidDataError("module has an entered grade, remove it before adding submodules")
    if module.passed:
        raise InvalidDataError("module is marked as passed without grade, unset passed before adding submodules")


def submodules_by_module() -> dict[int, list[db_schemas.SubmoduleResponse]]:
    grouped: dict[int, list[db_schemas.SubmoduleResponse]] = defaultdict(list)
    for submodule in db.list_all_submodules():
        grouped[submodule.module_id].append(submodule)
    return grouped
