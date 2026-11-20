from .database import DatabaseAPI
from .exceptions import DatabaseNotStartedError, NotFoundError
from .SQLite import SQLiteDatabase

db: type[DatabaseAPI] = SQLiteDatabase

__all__ = ["DatabaseAPI", "DatabaseNotStartedError", "NotFoundError", "SQLiteDatabase", "db"]
