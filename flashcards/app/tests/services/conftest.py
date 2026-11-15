import importlib
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from Database import SQLiteDatabase
from Routers.schemas import CardCreate, DeckCreate, ExamCreate
from Services import cards, decks, exams

sqlite_module = importlib.import_module("Database.SQLite")
database_module = importlib.import_module("Database.database")

EXAM_DATE = datetime(2026, 7, 1, 12, 0, tzinfo=timezone.utc)


@pytest.fixture
def isolated_paths(tmp_path, monkeypatch):
    monkeypatch.setattr(database_module, "DATA_DIR", tmp_path / "data")
    monkeypatch.setattr(database_module, "UPLOAD_DIR", tmp_path / "uploads")
    monkeypatch.setattr(sqlite_module, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(sqlite_module, "DATABASE_URL", f"sqlite:///{tmp_path / 'test.db'}")
    monkeypatch.setattr(SQLiteDatabase, "_session_factory", None)
    return tmp_path


@pytest.fixture
def started(isolated_paths):
    import Services

    Services.start()
    yield isolated_paths
    SQLiteDatabase._session_factory.kw["bind"].dispose()


@pytest.fixture
def client(isolated_paths):
    from main import app

    with TestClient(app) as test_client:
        yield test_client
    SQLiteDatabase._session_factory.kw["bind"].dispose()


@pytest.fixture
def make_exam(started):
    def _make(name="Mathe", exam_date=EXAM_DATE + timedelta(days=30), description=None):
        return exams.create_exam(ExamCreate(name=name, exam_date=exam_date, description=description))

    return _make


@pytest.fixture
def make_deck(started):
    def _make(exam_id=None, name="Deck", description=None):
        return decks.create_deck(DeckCreate(exam_id=exam_id, name=name, description=description))

    return _make


@pytest.fixture
def make_card(started):
    def _make(deck_id, front="Frage", back="Antwort", **kwargs):
        return cards.create_card(CardCreate(deck_id=deck_id, front=front, back=back, **kwargs))

    return _make
