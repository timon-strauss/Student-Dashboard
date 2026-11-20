from collections import defaultdict
from collections.abc import Iterable

from app.Database import db
from app.Database import schemas as db_schemas
from app.Routers.schemas import GradeSummary, ModuleProgress, YearProgress

from ._errors import translate_errors
from ._grading import resolve, submodules_by_module

GradedModule = tuple[db_schemas.ModuleResponse, float]


def _graded(modules: Iterable[db_schemas.ModuleResponse]) -> list[GradedModule]:
    submodules = submodules_by_module()
    graded = []
    for module in modules:
        result = resolve(module, submodules[module.id])
        if result.passed and result.grade is not None:
            graded.append((module, result.grade))
    return graded


def _ects(modules: Iterable[GradedModule]) -> int:
    return sum(module.ects for module, _ in modules)


def _weighted_grade(modules: Iterable[GradedModule]) -> float | None:
    modules = list(modules)
    total = _ects(modules)
    if total == 0:
        return None
    return round(sum(grade * module.ects for module, grade in modules) / total, 2)


def _summary(modules: list[GradedModule]) -> GradeSummary:
    return GradeSummary(grade=_weighted_grade(modules), ects=_ects(modules))


@translate_errors
def get_overall_grade() -> GradeSummary:
    return _summary(_graded(db.list_all_modules()))


@translate_errors
def get_year_grade(year_id: int) -> GradeSummary:
    return _summary(_graded(db.list_modules(year_id)))


@translate_errors
def get_progression() -> list[YearProgress]:
    by_year: dict[int, list[GradedModule]] = defaultdict(list)
    for module, grade in _graded(db.list_all_modules()):
        by_year[module.year_id].append((module, grade))

    progression = []
    so_far: list[GradedModule] = []
    for year in db.list_years():
        modules = by_year[year.id]
        so_far.extend(modules)
        progression.append(
            YearProgress(
                year_id=year.id,
                year=year.year,
                grade=_weighted_grade(modules),
                ects=_ects(modules),
                cumulative_grade=_weighted_grade(so_far),
                cumulative_ects=_ects(so_far),
            )
        )
    return progression


@translate_errors
def get_module_progress(module_id: int) -> ModuleProgress:
    submodules = db.list_submodules(module_id)
    graded = [s for s in submodules if s.reached_points is not None]
    graded_weight = sum(s.weight for s in graded)
    total_weight = sum(s.weight for s in submodules)
    percentage = None
    if graded_weight > 0:
        share = sum(s.weight * s.reached_points / s.max_points for s in graded) / graded_weight
        percentage = round(share * 100, 2)
    return ModuleProgress(reached_percentage=percentage, graded_weight=graded_weight, total_weight=total_weight)
