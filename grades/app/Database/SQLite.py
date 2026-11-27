from pathlib import Path

from pydantic import ValidationError
from sqlalchemy import Engine, create_engine, event, func, inspect, make_url, select, update
from sqlalchemy.orm import Session, sessionmaker

from .database import DATABASE_URL, PROJECT_ROOT, DatabaseAPI, create_folders
from .exceptions import DatabaseNotStartedError, InvalidDataError, NotFoundError
from .models import Base, Module, Submodule, Year
from .schemas import (
    ModuleCreate,
    ModuleResponse,
    ModuleUpdate,
    SubmoduleBase,
    SubmoduleCreate,
    SubmoduleResponse,
    SubmoduleUpdate,
    YearCreate,
    YearResponse,
    YearUpdate,
)


class SQLiteDatabase(DatabaseAPI):
    _session_factory: sessionmaker | None = None

    @staticmethod
    def _enable_foreign_keys(connection, _):
        connection.execute("PRAGMA foreign_keys=ON")

    @classmethod
    def db_start(cls) -> None:
        create_folders()
        url = make_url(DATABASE_URL)
        if url.database and url.database != ":memory:":
            db_path = Path(url.database)
            if not db_path.is_absolute():
                db_path = (PROJECT_ROOT / db_path).resolve()
                url = url.set(database=str(db_path))
            db_path.parent.mkdir(parents=True, exist_ok=True)
        engine = create_engine(url)
        event.listen(engine, "connect", cls._enable_foreign_keys)
        Base.metadata.create_all(engine)
        cls._drop_submodule_weight(engine)
        cls._session_factory = sessionmaker(bind=engine)

    @staticmethod
    def _drop_submodule_weight(engine: Engine) -> None:
        columns = {column["name"] for column in inspect(engine).get_columns("submodules")}
        if "weight" not in columns:
            return
        with engine.begin() as connection:
            connection.exec_driver_sql("ALTER TABLE submodules RENAME TO submodules_old")
            connection.exec_driver_sql("DROP INDEX IF EXISTS ix_submodules_module_id")
            Submodule.__table__.create(connection)
            connection.exec_driver_sql(
                "INSERT INTO submodules (id, module_id, name, max_points, reached_points) "
                "SELECT id, module_id, name, max_points, reached_points FROM submodules_old"
            )
            connection.exec_driver_sql("DROP TABLE submodules_old")

    @classmethod
    def _session(cls) -> Session:
        if cls._session_factory is None:
            raise DatabaseNotStartedError()
        return cls._session_factory()

    # --- Years ---

    @classmethod
    def list_years(cls) -> list[YearResponse]:
        with cls._session() as session:
            years = session.scalars(select(Year).order_by(Year.position))
            return [YearResponse.model_validate(y) for y in years]

    @classmethod
    def get_year(cls, year_id: int) -> YearResponse:
        with cls._session() as session:
            year = session.get(Year, year_id)
            if year is None:
                raise NotFoundError("Year", year_id)
            return YearResponse.model_validate(year)

    @classmethod
    def create_year(cls, data: YearCreate) -> YearResponse:
        with cls._session() as session:
            year = Year(**data.model_dump(), position=cls._year_count(session))
            session.add(year)
            session.commit()
            session.refresh(year)
            return YearResponse.model_validate(year)

    @classmethod
    def update_year(cls, year_id: int, data: YearUpdate) -> YearResponse:
        with cls._session() as session:
            year = session.get(Year, year_id)
            if year is None:
                raise NotFoundError("Year", year_id)
            for field, value in data.model_dump(exclude_unset=True).items():
                setattr(year, field, value)
            session.commit()
            session.refresh(year)
            return YearResponse.model_validate(year)

    @classmethod
    def reposition_year(cls, year_id: int, position: int) -> YearResponse:
        with cls._session() as session:
            year = session.get(Year, year_id)
            if year is None:
                raise NotFoundError("Year", year_id)
            old = year.position
            new = max(0, min(position, cls._year_count(session) - 1))
            if new < old:
                session.execute(
                    update(Year)
                    .where(Year.position >= new, Year.position < old)
                    .values(position=Year.position + 1)
                )
            elif new > old:
                session.execute(
                    update(Year)
                    .where(Year.position > old, Year.position <= new)
                    .values(position=Year.position - 1)
                )
            year.position = new
            session.commit()
            session.refresh(year)
            return YearResponse.model_validate(year)

    @classmethod
    def delete_year(cls, year_id: int) -> None:
        with cls._session() as session:
            year = session.get(Year, year_id)
            if year is None:
                raise NotFoundError("Year", year_id)
            position = year.position
            session.delete(year)
            session.flush()
            session.execute(
                update(Year).where(Year.position > position).values(position=Year.position - 1)
            )
            session.commit()

    @staticmethod
    def _year_count(session: Session) -> int:
        return session.scalar(select(func.count()).select_from(Year))

    # --- Modules ---

    @classmethod
    def list_modules(cls, year_id: int) -> list[ModuleResponse]:
        with cls._session() as session:
            if session.get(Year, year_id) is None:
                raise NotFoundError("Year", year_id)
            modules = session.scalars(
                select(Module).where(Module.year_id == year_id).order_by(Module.id)
            )
            return [ModuleResponse.model_validate(m) for m in modules]

    @classmethod
    def list_all_modules(cls) -> list[ModuleResponse]:
        with cls._session() as session:
            modules = session.scalars(
                select(Module).join(Year).order_by(Year.position, Module.id)
            )
            return [ModuleResponse.model_validate(m) for m in modules]

    @classmethod
    def get_module(cls, module_id: int) -> ModuleResponse:
        with cls._session() as session:
            module = session.get(Module, module_id)
            if module is None:
                raise NotFoundError("Module", module_id)
            return ModuleResponse.model_validate(module)

    @classmethod
    def create_module(cls, data: ModuleCreate) -> ModuleResponse:
        with cls._session() as session:
            if session.get(Year, data.year_id) is None:
                raise NotFoundError("Year", data.year_id)
            module = Module(**data.model_dump())
            session.add(module)
            session.commit()
            session.refresh(module)
            return ModuleResponse.model_validate(module)

    @classmethod
    def update_module(cls, module_id: int, data: ModuleUpdate) -> ModuleResponse:
        with cls._session() as session:
            module = session.get(Module, module_id)
            if module is None:
                raise NotFoundError("Module", module_id)
            changes = data.model_dump(exclude_unset=True)
            new_year_id = changes.get("year_id")
            if new_year_id is not None and session.get(Year, new_year_id) is None:
                raise NotFoundError("Year", new_year_id)
            for field, value in changes.items():
                setattr(module, field, value)
            session.commit()
            session.refresh(module)
            return ModuleResponse.model_validate(module)

    @classmethod
    def delete_module(cls, module_id: int) -> None:
        with cls._session() as session:
            module = session.get(Module, module_id)
            if module is None:
                raise NotFoundError("Module", module_id)
            session.delete(module)
            session.commit()

    # --- Submodules ---

    @classmethod
    def list_submodules(cls, module_id: int) -> list[SubmoduleResponse]:
        with cls._session() as session:
            if session.get(Module, module_id) is None:
                raise NotFoundError("Module", module_id)
            submodules = session.scalars(
                select(Submodule).where(Submodule.module_id == module_id).order_by(Submodule.id)
            )
            return [SubmoduleResponse.model_validate(s) for s in submodules]

    @classmethod
    def list_all_submodules(cls) -> list[SubmoduleResponse]:
        with cls._session() as session:
            submodules = session.scalars(select(Submodule).order_by(Submodule.module_id, Submodule.id))
            return [SubmoduleResponse.model_validate(s) for s in submodules]

    @classmethod
    def get_submodule(cls, submodule_id: int) -> SubmoduleResponse:
        with cls._session() as session:
            submodule = session.get(Submodule, submodule_id)
            if submodule is None:
                raise NotFoundError("Submodule", submodule_id)
            return SubmoduleResponse.model_validate(submodule)

    @classmethod
    def create_submodule(cls, data: SubmoduleCreate) -> SubmoduleResponse:
        with cls._session() as session:
            if session.get(Module, data.module_id) is None:
                raise NotFoundError("Module", data.module_id)
            submodule = Submodule(**data.model_dump())
            session.add(submodule)
            session.commit()
            session.refresh(submodule)
            return SubmoduleResponse.model_validate(submodule)

    @classmethod
    def update_submodule(cls, submodule_id: int, data: SubmoduleUpdate) -> SubmoduleResponse:
        with cls._session() as session:
            submodule = session.get(Submodule, submodule_id)
            if submodule is None:
                raise NotFoundError("Submodule", submodule_id)
            changes = data.model_dump(exclude_unset=True)
            current = SubmoduleResponse.model_validate(submodule).model_dump(exclude={"id"})
            try:
                SubmoduleBase.model_validate({**current, **changes})
            except ValidationError as error:
                raise InvalidDataError(error.errors()[0]["msg"]) from error
            for field, value in changes.items():
                setattr(submodule, field, value)
            session.commit()
            session.refresh(submodule)
            return SubmoduleResponse.model_validate(submodule)

    @classmethod
    def delete_submodule(cls, submodule_id: int) -> None:
        with cls._session() as session:
            submodule = session.get(Submodule, submodule_id)
            if submodule is None:
                raise NotFoundError("Submodule", submodule_id)
            session.delete(submodule)
            session.commit()
