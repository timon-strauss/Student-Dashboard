from collections.abc import Callable
from functools import wraps
from typing import ParamSpec, TypeVar

from app.Database import InvalidDataError as DatabaseInvalidDataError
from app.Database import NotFoundError as DatabaseNotFoundError

from .exceptions import InvalidDataError, NotFoundError

P = ParamSpec("P")
R = TypeVar("R")


def translate_errors(func: Callable[P, R]) -> Callable[P, R]:
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        try:
            return func(*args, **kwargs)
        except DatabaseNotFoundError as error:
            raise NotFoundError(error.entity, error.entity_id) from error
        except DatabaseInvalidDataError as error:
            raise InvalidDataError(str(error)) from error

    return wrapper
