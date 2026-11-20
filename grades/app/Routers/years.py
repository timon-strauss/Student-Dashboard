from fastapi import APIRouter, status

from app.Services import years as year_service

from .schemas import YearCreate, YearReposition, YearResponse, YearUpdate

router = APIRouter(prefix="/years", tags=["years"])


@router.get("", response_model=list[YearResponse])
def list_years() -> list[YearResponse]:
    return year_service.list_years()


@router.post("", response_model=YearResponse, status_code=status.HTTP_201_CREATED)
def create_year(data: YearCreate) -> YearResponse:
    return year_service.create_year(data)


@router.get("/{year_id}", response_model=YearResponse)
def get_year(year_id: int) -> YearResponse:
    return year_service.get_year(year_id)


@router.patch("/{year_id}", response_model=YearResponse)
def update_year(year_id: int, data: YearUpdate) -> YearResponse:
    return year_service.update_year(year_id, data)


@router.put("/{year_id}/position", response_model=YearResponse)
def reposition_year(year_id: int, data: YearReposition) -> YearResponse:
    return year_service.reposition_year(year_id, data.position)


@router.delete("/{year_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_year(year_id: int) -> None:
    year_service.delete_year(year_id)
