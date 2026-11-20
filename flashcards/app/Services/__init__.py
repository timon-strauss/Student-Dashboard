from app.Database import db

from . import cards, config, decks, exams, images, scheduler, statistics, transfers
from .exceptions import InvalidImageError, NotFoundError


def start() -> None:
    config.validate()
    db.db_start()


__all__ = ["InvalidImageError", "NotFoundError", "cards", "config", "decks", "exams", "images", "scheduler", "start", "statistics", "transfers"]
