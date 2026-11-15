import os
from pathlib import Path
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_DATA_DIR = Path(os.getenv("DATA_DIR", str(_PROJECT_ROOT / "data")))
_UPLOADS_DIR = Path(os.getenv("UPLOAD_DIR", str(_PROJECT_ROOT / "Upload")))

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{_DATA_DIR / 'flashcards.db'}")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

if engine.dialect.name == "sqlite":
    # SQLite ignores foreign keys (and ON DELETE CASCADE) unless enabled per connection
    @event.listens_for(engine, "connect")
    def _enable_sqlite_foreign_keys(dbapi_connection, _):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal =sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def start_db():
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    _UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
