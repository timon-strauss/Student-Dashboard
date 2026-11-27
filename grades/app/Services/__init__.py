from app.Database import db

from . import grading, modules, statistics, submodules, years
from .exceptions import InvalidDataError, NotFoundError


def start() -> None:
    db.db_start()


__all__ = ["InvalidDataError", "NotFoundError", "grading", "modules", "start", "statistics", "submodules", "years"]
