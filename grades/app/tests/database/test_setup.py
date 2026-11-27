import pytest
from sqlalchemy import create_engine, inspect

from app.Database import DatabaseNotStartedError, SQLiteDatabase, db
from app.Database.schemas import SubmoduleCreate


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


def test_start_drops_legacy_submodule_weight(start_db, isolated_paths):
    url = f"sqlite:///{isolated_paths / 'legacy.db'}"
    engine = create_engine(url)
    with engine.begin() as connection:
        connection.exec_driver_sql("CREATE TABLE years (id INTEGER PRIMARY KEY, year VARCHAR NOT NULL, position INTEGER NOT NULL)")
        connection.exec_driver_sql(
            "CREATE TABLE modules (id INTEGER PRIMARY KEY, year_id INTEGER NOT NULL REFERENCES years (id) ON DELETE CASCADE, "
            "name VARCHAR NOT NULL, grade FLOAT, ects INTEGER NOT NULL, passed BOOLEAN NOT NULL)"
        )
        connection.exec_driver_sql(
            "CREATE TABLE submodules (id INTEGER PRIMARY KEY, module_id INTEGER NOT NULL REFERENCES modules (id) ON DELETE CASCADE, "
            "name VARCHAR NOT NULL, max_points FLOAT NOT NULL, reached_points FLOAT, weight FLOAT NOT NULL, "
            "CONSTRAINT ck_submodules_weight CHECK (weight > 0))"
        )
        connection.exec_driver_sql("CREATE INDEX ix_submodules_module_id ON submodules (module_id)")
        connection.exec_driver_sql("INSERT INTO years VALUES (1, '2025', 0)")
        connection.exec_driver_sql("INSERT INTO modules VALUES (1, 1, 'm', NULL, 5, 0)")
        connection.exec_driver_sql("INSERT INTO submodules VALUES (7, 1, 'Klausur', 100, 80, 2)")
    engine.dispose()

    db = start_db(url)

    columns = {c["name"] for c in inspect(db._session_factory.kw["bind"]).get_columns("submodules")}
    assert columns == {"id", "module_id", "name", "max_points", "reached_points"}
    assert [(s.id, s.name, s.reached_points) for s in db.list_submodules(1)] == [(7, "Klausur", 80)]
    created = db.create_submodule(SubmoduleCreate(module_id=1, name="Übung", max_points=60))
    assert created.module_id == 1
    db.delete_year(1)
    assert db.list_all_submodules() == []


def test_start_twice_keeps_migrated_table(start_db, isolated_paths):
    url = f"sqlite:///{isolated_paths / 'test.db'}"
    start_db(url)

    assert "weight" not in {c["name"] for c in inspect(start_db(url)._session_factory.kw["bind"]).get_columns("submodules")}
