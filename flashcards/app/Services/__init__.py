from Database import db

from . import cards, decks, exams, images
from .exceptions import InvalidImageError, NotFoundError


def start() -> None:
    db.db_start()


__all__ = ["InvalidImageError", "NotFoundError", "cards", "decks", "exams", "images", "start"]
