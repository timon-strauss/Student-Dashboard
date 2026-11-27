from fastapi import APIRouter, Query, status

from app.Services import modules as module_service

from .schemas import ModuleCreate, ModuleResponse, ModuleUpdate

router = APIRouter(prefix="/modules", tags=["modules"])


@router.get("", response_model=list[ModuleResponse])
def list_modules(
    year_id: int | None = Query(default=None, description="Modules of this year; omitted returns all modules"),
) -> list[ModuleResponse]:
    return module_service.list_modules(year_id)


@router.post("", response_model=ModuleResponse, status_code=status.HTTP_201_CREATED)
def create_module(data: ModuleCreate) -> ModuleResponse:
    return module_service.create_module(data)


@router.get("/{module_id}", response_model=ModuleResponse)
def get_module(module_id: int) -> ModuleResponse:
    return module_service.get_module(module_id)


@router.patch("/{module_id}", response_model=ModuleResponse)
def update_module(module_id: int, data: ModuleUpdate) -> ModuleResponse:
    return module_service.update_module(module_id, data)


@router.delete("/{module_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_module(module_id: int) -> None:
    module_service.delete_module(module_id)
