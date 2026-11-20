from pathlib import Path

from sqlalchemy import create_engine, event, make_url
from sqlalchemy.orm import Session, sessionmaker

from .database import DATABASE_URL, PROJECT_ROOT, DatabaseAPI, create_folders
from .exceptions import DatabaseNotStartedError
from .models import Base


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
        cls._session_factory = sessionmaker(bind=engine)

    @classmethod
    def _session(cls) -> Session:
        if cls._session_factory is None:
            raise DatabaseNotStartedError()
        return cls._session_factory()
