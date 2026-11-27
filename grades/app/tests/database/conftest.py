import importlib

import pytest

from app.Database import SQLiteDatabase
from app.Database.schemas import ModuleCreate, SubmoduleCreate, YearCreate

sqlite_module = importlib.import_module("app.Database.SQLite")
database_module = importlib.import_module("app.Database.database")


@pytest.fixture
def isolated_paths(tmp_path, monkeypatch):
    monkeypatch.setattr(database_module, "DATA_DIR", tmp_path / "data")
    monkeypatch.setattr(sqlite_module, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(SQLiteDatabase, "_session_factory", None)
    return tmp_path


@pytest.fixture
def start_db(isolated_paths, monkeypatch):
    engines = []

    def _start(url: str):
        monkeypatch.setattr(sqlite_module, "DATABASE_URL", url)
        SQLiteDatabase.db_start()
        engines.append(SQLiteDatabase._session_factory.kw["bind"])
        return SQLiteDatabase

    yield _start
    for engine in engines:
        engine.dispose()


@pytest.fixture
def db(start_db, isolated_paths):
    return start_db(f"sqlite:///{isolated_paths / 'test.db'}")


@pytest.fixture
def make_year(db):
    def _make(year="2025"):
        return db.create_year(YearCreate(year=year))

    return _make


@pytest.fixture
def make_module(db):
    def _make(year_id, name="Analysis", ects=5, **kwargs):
        return db.create_module(ModuleCreate(year_id=year_id, name=name, ects=ects, **kwargs))

    return _make


@pytest.fixture
def make_submodule(db):
    def _make(module_id, name="Klausur", max_points=100.0, **kwargs):
        return db.create_submodule(
            SubmoduleCreate(module_id=module_id, name=name, max_points=max_points, **kwargs)
        )

    return _make
