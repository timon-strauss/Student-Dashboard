from app.Database import db

from . import modules, statistics, submodules, years
from .exceptions import InvalidDataError, NotFoundError


def start() -> None:
    db.db_start()


__all__ = ["InvalidDataError", "NotFoundError", "modules", "start", "statistics", "submodules", "years"]
