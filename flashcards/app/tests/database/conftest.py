import importlib
from datetime import datetime, timedelta, timezone

import pytest

from Database import SQLiteDatabase
from Database.models import Card
from Database.schemas import CardCreate, DeckCreate, ExamCreate

sqlite_module = importlib.import_module("Database.SQLite")
database_module = importlib.import_module("Database.database")

NOW = datetime(2026, 6, 1, 12, 0, tzinfo=timezone.utc)


@pytest.fixture
def isolated_paths(tmp_path, monkeypatch):
    monkeypatch.setattr(database_module, "DATA_DIR", tmp_path / "data")
    monkeypatch.setattr(database_module, "UPLOAD_DIR", tmp_path / "uploads")
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
def make_exam(db):
    def _make(name="Mathe", exam_date=NOW + timedelta(days=30), description=None):
        return db.create_exam(
            ExamCreate(name=name, exam_date=exam_date, description=description)
        )

    return _make


@pytest.fixture
def make_deck(db):
    def _make(exam_id=None, name="Deck", description=None):
        return db.create_deck(
            DeckCreate(exam_id=exam_id, name=name, description=description)
        )

    return _make


@pytest.fixture
def make_card(db):
    def _make(deck_id, front="Frage", back="Antwort", **kwargs):
        return db.create_card(
            CardCreate(deck_id=deck_id, front=front, back=back, **kwargs)
        )

    return _make


@pytest.fixture
def set_due(db):
    def _set(card_id, due):
        with db._session() as session:
            session.get(Card, card_id).due = due
            session.commit()

    return _set
