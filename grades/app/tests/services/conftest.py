import importlib

import pytest
from fastapi.testclient import TestClient

from app.Database import SQLiteDatabase

sqlite_module = importlib.import_module("app.Database.SQLite")
database_module = importlib.import_module("app.Database.database")


@pytest.fixture
def isolated_paths(tmp_path, monkeypatch):
    monkeypatch.setattr(database_module, "DATA_DIR", tmp_path / "data")
    monkeypatch.setattr(sqlite_module, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(sqlite_module, "DATABASE_URL", f"sqlite:///{tmp_path / 'test.db'}")
    monkeypatch.setattr(SQLiteDatabase, "_session_factory", None)
    return tmp_path


@pytest.fixture
def client(isolated_paths):
    from app.main import app

    with TestClient(app) as test_client:
        yield test_client
    SQLiteDatabase._session_factory.kw["bind"].dispose()
