from app.Database import db

from .exceptions import NotFoundError


def start() -> None:
    db.db_start()


__all__ = ["NotFoundError", "start"]
