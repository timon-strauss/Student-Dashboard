import pytest
from sqlalchemy import inspect

from app.Database import DatabaseNotStartedError, SQLiteDatabase, db


def test_db_is_sqlite():
    assert db is SQLiteDatabase


def test_session_before_start_raises(isolated_paths):
    with pytest.raises(DatabaseNotStartedError):
        SQLiteDatabase._session()


def test_start_creates_tables(db):
    engine = db._session_factory.kw["bind"]

    assert set(inspect(engine).get_table_names()) == {"years", "modules", "submodules"}


def test_start_creates_data_folder(db, isolated_paths):
    assert (isolated_paths / "data").is_dir()


def test_relative_url_resolves_against_project_root(start_db, isolated_paths):
    start_db("sqlite:///relative/grades.db")

    assert (isolated_paths / "relative" / "grades.db").exists()


def test_foreign_keys_enabled(db):
    with db._session() as session:
        assert session.connection().exec_driver_sql("PRAGMA foreign_keys").scalar() == 1
