from .database import DatabaseAPI
from .exceptions import DatabaseNotStartedError, InvalidDataError, NotFoundError
from .SQLite import SQLiteDatabase

db: type[DatabaseAPI] = SQLiteDatabase

__all__ = ["DatabaseAPI", "DatabaseNotStartedError", "InvalidDataError", "NotFoundError", "SQLiteDatabase", "db"]
