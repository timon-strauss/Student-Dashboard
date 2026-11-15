import os
import subprocess
import sys
from pathlib import Path

import pytest
from sqlalchemy import make_url

import Database
from Database import DatabaseAPI, DatabaseNotStartedError, SQLiteDatabase
from Database.schemas import ExamCreate

from .conftest import NOW, database_module

APP_DIR = Path(database_module.__file__).resolve().parents[1]


class TestPackage:
    def test_default_backend_is_sqlite(self):
        assert Database.db is SQLiteDatabase

    def test_public_exports(self):
        assert set(Database.__all__) == {
            "DatabaseAPI",
            "DatabaseNotStartedError",
            "NotFoundError",
            "SQLiteDatabase",
            "db",
        }

    def test_sqlite_implements_full_api(self):
        assert issubclass(SQLiteDatabase, DatabaseAPI)
        assert not SQLiteDatabase.__abstractmethods__

    def test_api_is_abstract(self):
        with pytest.raises(TypeError):
            DatabaseAPI()

    def test_incomplete_backend_cannot_be_instantiated(self):
        class Incomplete(DatabaseAPI):
            @classmethod
            def db_start(cls):
                pass

        with pytest.raises(TypeError):
            Incomplete()


class TestConfig:
    def test_project_root_points_to_repository(self):
        assert (database_module.PROJECT_ROOT / "flashcards" / "app" / "Database").is_dir()

    def test_create_folders(self, isolated_paths):
        database_module.create_folders()
        database_module.create_folders()

        assert (isolated_paths / "data").is_dir()
        assert (isolated_paths / "uploads").is_dir()

    def test_paths_derived_from_project_root(self):
        root = database_module.PROJECT_ROOT

        assert database_module.DATA_DIR == root / "data"
        assert database_module.UPLOAD_DIR == root / "uploads"

    def test_database_url_points_to_absolute_sqlite_file(self):
        url = make_url(database_module.DATABASE_URL)

        assert isinstance(database_module.DATABASE_URL, str)
        assert url.drivername == "sqlite"
        assert Path(url.database) == database_module.DATA_DIR / "flashcards.db"
        assert Path(url.database).is_absolute()

    def test_config_ignores_environment(self, tmp_path):
        script = (
            "from Database import database as d;"
            "print(d.DATA_DIR); print(d.UPLOAD_DIR); print(d.DATABASE_URL)"
        )
        env = dict(
            os.environ,
            DATA_DIR=str(tmp_path / "d"),
            UPLOAD_DIR=str(tmp_path / "u"),
            DATABASE_URL="sqlite:///custom.db",
        )

        result = subprocess.run(
            [sys.executable, "-c", script],
            cwd=APP_DIR,
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )

        assert result.stdout.splitlines() == [
            str(database_module.DATA_DIR),
            str(database_module.UPLOAD_DIR),
            database_module.DATABASE_URL,
        ]


class TestDbStart:
    def test_session_before_start_raises(self, isolated_paths):
        with pytest.raises(DatabaseNotStartedError):
            SQLiteDatabase.list_exams()

    def test_start_creates_folders_and_file(self, start_db, isolated_paths):
        db_file = isolated_paths / "nested" / "dir" / "app.db"

        start_db(f"sqlite:///{db_file}")

        assert db_file.is_file()
        assert (isolated_paths / "data").is_dir()
        assert (isolated_paths / "uploads").is_dir()

    def test_relative_path_resolved_against_project_root(self, start_db, isolated_paths):
        db = start_db("sqlite:///./rel/flashcards.db")
        db.create_exam(ExamCreate(name="x", exam_date=NOW))

        assert (isolated_paths / "rel" / "flashcards.db").is_file()

    @pytest.mark.parametrize("url", ["sqlite:///:memory:", "sqlite://"])
    def test_in_memory_database(self, start_db, isolated_paths, url):
        db = start_db(url)
        db.create_exam(ExamCreate(name="x", exam_date=NOW))

        assert [e.name for e in db.list_exams()] == ["x"]
        assert not any(isolated_paths.glob("*.db"))

    def test_data_persists_across_restart(self, start_db, isolated_paths):
        url = f"sqlite:///{isolated_paths / 'persist.db'}"
        start_db(url).create_exam(ExamCreate(name="x", exam_date=NOW))

        db = start_db(url)

        assert [e.name for e in db.list_exams()] == ["x"]

    def test_restart_is_idempotent_for_schema(self, db, start_db, isolated_paths):
        db.create_exam(ExamCreate(name="x", exam_date=NOW))

        start_db(f"sqlite:///{isolated_paths / 'test.db'}")

        assert len(db.list_exams()) == 1
