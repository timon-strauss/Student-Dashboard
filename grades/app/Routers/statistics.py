from fastapi import APIRouter

from app.Services import statistics as statistics_service

from .schemas import GradeSummary, ModuleProgress, YearProgress

router = APIRouter(prefix="/statistics", tags=["statistics"])


@router.get(
    "/overall",
    response_model=GradeSummary,
    description="Sum of grade * ECTS over all passed modules with a grade, divided by their ECTS; modules without grade are ignored",
)
def get_overall_grade() -> GradeSummary:
    return statistics_service.get_overall_grade()


@router.get(
    "/years/{year_id}",
    response_model=GradeSummary,
    description="Like overall, restricted to the modules of this year",
)
def get_year_grade(year_id: int) -> GradeSummary:
    return statistics_service.get_year_grade(year_id)


@router.get(
    "/progression",
    response_model=list[YearProgress],
    description="One point per year in year order, with running totals up to that year",
)
def get_progression() -> list[YearProgress]:
    return statistics_service.get_progression()


@router.get(
    "/modules/{module_id}",
    response_model=ModuleProgress,
    description="Weighted share of reached points over the submodules that have reached points",
)
def get_module_progress(module_id: int) -> ModuleProgress:
    return statistics_service.get_module_progress(module_id)
