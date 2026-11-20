from abc import ABC, abstractmethod
from pathlib import Path

from .schemas import (
    ModuleCreate,
    ModuleResponse,
    ModuleUpdate,
    SubmoduleCreate,
    SubmoduleResponse,
    SubmoduleUpdate,
    YearCreate,
    YearResponse,
    YearUpdate,
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]

DATA_DIR = PROJECT_ROOT / "data"
DATABASE_URL = f"sqlite:///{DATA_DIR / 'grades.db'}"


def create_folders() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


class DatabaseAPI(ABC):
    @classmethod
    @abstractmethod
    def db_start(cls) -> None:
        ...

    # --- Years ---

    @classmethod
    @abstractmethod
    def list_years(cls) -> list[YearResponse]:
        ...

    @classmethod
    @abstractmethod
    def get_year(cls, year_id: int) -> YearResponse:
        ...

    @classmethod
    @abstractmethod
    def create_year(cls, data: YearCreate) -> YearResponse:
        ...

    @classmethod
    @abstractmethod
    def update_year(cls, year_id: int, data: YearUpdate) -> YearResponse:
        ...

    @classmethod
    @abstractmethod
    def reposition_year(cls, year_id: int, position: int) -> YearResponse:
        ...

    @classmethod
    @abstractmethod
    def delete_year(cls, year_id: int) -> None:
        ...

    # --- Modules ---

    @classmethod
    @abstractmethod
    def list_modules(cls, year_id: int) -> list[ModuleResponse]:
        ...

    @classmethod
    @abstractmethod
    def list_all_modules(cls) -> list[ModuleResponse]:
        ...

    @classmethod
    @abstractmethod
    def get_module(cls, module_id: int) -> ModuleResponse:
        ...

    @classmethod
    @abstractmethod
    def create_module(cls, data: ModuleCreate) -> ModuleResponse:
        ...

    @classmethod
    @abstractmethod
    def update_module(cls, module_id: int, data: ModuleUpdate) -> ModuleResponse:
        ...

    @classmethod
    @abstractmethod
    def delete_module(cls, module_id: int) -> None:
        ...

    # --- Submodules ---

    @classmethod
    @abstractmethod
    def list_submodules(cls, module_id: int) -> list[SubmoduleResponse]:
        ...

    @classmethod
    @abstractmethod
    def get_submodule(cls, submodule_id: int) -> SubmoduleResponse:
        ...

    @classmethod
    @abstractmethod
    def create_submodule(cls, data: SubmoduleCreate) -> SubmoduleResponse:
        ...

    @classmethod
    @abstractmethod
    def update_submodule(cls, submodule_id: int, data: SubmoduleUpdate) -> SubmoduleResponse:
        ...

    @classmethod
    @abstractmethod
    def delete_submodule(cls, submodule_id: int) -> None:
        ...
