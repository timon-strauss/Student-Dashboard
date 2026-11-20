from fastapi import APIRouter

from app.Services import grading as grading_service

router = APIRouter(prefix="/grading", tags=["grading"])


@router.get(
    "/max-points",
    response_model=list[int],
    description="Max points that have a grade table; submodules must use one of these",
)
def list_supported_max_points() -> list[int]:
    return grading_service.supported_max_points()
