import mimetypes
from pathlib import Path, PurePath

from Database import NotFoundError as DatabaseNotFoundError
from Database import db

from ._errors import translate_errors
from .exceptions import InvalidImageError


def _extension(filename: str | None, content_type: str | None) -> str:
    suffix = PurePath(filename or "").suffix.lower()
    if content_type and content_type.startswith("image/"):
        if suffix and mimetypes.guess_type(f"image{suffix}")[0] == content_type:
            return suffix
        guessed = mimetypes.guess_extension(content_type)
        if guessed:
            return guessed
    if suffix:
        return suffix
    raise InvalidImageError("Could not determine image file extension")


@translate_errors
def save_image(data: bytes, filename: str | None, content_type: str | None) -> str:
    if not data:
        raise InvalidImageError("Image is empty")
    try:
        return db.save_image(data, _extension(filename, content_type))
    except ValueError as error:
        raise InvalidImageError(str(error)) from error


@translate_errors
def get_image_path(name: str) -> Path:
    return db.get_image_path(name)


def extension_for(media_type: str) -> str:
    return _extension(None, media_type)


def read_image(name: str) -> tuple[bytes, str] | None:
    try:
        path = db.get_image_path(name)
        data = path.read_bytes()
    except (DatabaseNotFoundError, OSError):
        return None
    media_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    return data, media_type
