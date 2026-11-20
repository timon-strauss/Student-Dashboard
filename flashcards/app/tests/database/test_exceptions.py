import pytest

from app.Database import DatabaseNotStartedError, NotFoundError


def test_not_found_error_message_and_attributes():
    error = NotFoundError("Deck", 42)

    assert str(error) == "Deck with id 42 not found"
    assert error.entity == "Deck"
    assert error.entity_id == 42


def test_not_found_error_is_exception():
    with pytest.raises(Exception):
        raise NotFoundError("Card", 1)


def test_database_not_started_error_message():
    assert str(DatabaseNotStartedError()) == "Database not started, call db_start() first"
