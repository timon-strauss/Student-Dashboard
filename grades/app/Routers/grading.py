from fastapi import APIRouter

from app.Services import grading as grading_service

router = APIRouter(prefix="/grading", tags=["grading"])


@router.get(
    "/max-points",
    response_model=list[int],
    description="Max points that have a grade table; a module grade needs its submodules to sum up to one of these",
)
def list_supported_max_points() -> list[int]:
    return grading_service.supported_max_points()
