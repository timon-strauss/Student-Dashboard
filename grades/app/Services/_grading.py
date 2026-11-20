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
    reached_points: float | None
    max_points: float | None


def total_points(submodules: Iterable[db_schemas.SubmoduleResponse]) -> tuple[float, float]:
    submodules = list(submodules)
    reached = sum(s.reached_points for s in submodules if s.reached_points is not None)
    return reached, sum(s.max_points for s in submodules)


def module_grade(submodules: Iterable[db_schemas.SubmoduleResponse]) -> float | None:
    submodules = list(submodules)
    if not submodules or any(s.reached_points is None for s in submodules):
        return None
    reached, maximum = total_points(submodules)
    if not Grading.is_supported(maximum):
        return None
    return Grading.grade_for(maximum, reached)


def resolve(
    module: db_schemas.ModuleResponse, submodules: list[db_schemas.SubmoduleResponse]
) -> ModuleResult:
    if submodules:
        grade = module_grade(submodules)
        reached, maximum = total_points(submodules)
    else:
        grade, reached, maximum = module.grade, None, None
    passed = grade <= PASSING_GRADE if grade is not None else module.passed
    return ModuleResult(
        grade=grade,
        passed=passed,
        grade_from_submodules=bool(submodules),
        reached_points=reached,
        max_points=maximum,
    )


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
