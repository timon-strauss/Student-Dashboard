from fastapi import APIRouter, Query, status

from app.Services import submodules as submodule_service

from .schemas import SubmoduleCreate, SubmoduleResponse, SubmoduleUpdate

router = APIRouter(prefix="/submodules", tags=["submodules"])


@router.get("", response_model=list[SubmoduleResponse])
def list_submodules(
    module_id: int = Query(description="Submodules of this module"),
) -> list[SubmoduleResponse]:
    return submodule_service.list_submodules(module_id)


@router.post("", response_model=SubmoduleResponse, status_code=status.HTTP_201_CREATED)
def create_submodule(data: SubmoduleCreate) -> SubmoduleResponse:
    return submodule_service.create_submodule(data)


@router.get("/{submodule_id}", response_model=SubmoduleResponse)
def get_submodule(submodule_id: int) -> SubmoduleResponse:
    return submodule_service.get_submodule(submodule_id)


@router.patch("/{submodule_id}", response_model=SubmoduleResponse)
def update_submodule(submodule_id: int, data: SubmoduleUpdate) -> SubmoduleResponse:
    return submodule_service.update_submodule(submodule_id, data)


@router.delete("/{submodule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_submodule(submodule_id: int) -> None:
    submodule_service.delete_submodule(submodule_id)
