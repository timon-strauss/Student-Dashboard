from datetime import datetime, timezone

import pytest

from Routers.schemas import CardResponse, CardUpdate, DeckResponse, DeckUpdate, ExamResponse, ExamUpdate
from Services import InvalidImageError, NotFoundError, cards, decks, exams, images


def test_exam_crud(make_exam):
    exam = make_exam(description="Analysis")
    assert isinstance(exam, ExamResponse)
    assert exams.get_exam(exam.id) == exam
    assert exams.list_exams() == [exam]

    updated = exams.update_exam(exam.id, ExamUpdate(name="Physik"))
    assert updated.name == "Physik"
    assert updated.description == "Analysis"

    cleared = exams.update_exam(exam.id, ExamUpdate(description=None))
    assert cleared.description is None

    exams.delete_exam(exam.id)
    assert exams.list_exams() == []


def test_exam_not_found(started):
    with pytest.raises(NotFoundError) as error:
        exams.get_exam(42)
    assert error.value.entity == "Exam"
    assert error.value.entity_id == 42
    with pytest.raises(NotFoundError):
        exams.update_exam(42, ExamUpdate(name="x"))
    with pytest.raises(NotFoundError):
        exams.delete_exam(42)


def test_deck_crud(make_exam, make_deck):
    exam = make_exam()
    loose = make_deck(name="Lose")
    bound = make_deck(exam_id=exam.id, name="Gebunden")
    assert isinstance(bound, DeckResponse)
    assert decks.list_decks(None) == [loose]
    assert decks.list_decks(exam.id) == [bound]
    assert decks.get_deck(bound.id) == bound

    moved = decks.update_deck(bound.id, DeckUpdate(exam_id=None))
    assert moved.exam_id is None
    assert moved.name == "Gebunden"

    decks.delete_deck(loose.id)
    with pytest.raises(NotFoundError):
        decks.get_deck(loose.id)


def test_deck_unknown_exam(started):
    with pytest.raises(NotFoundError) as error:
        decks.list_decks(7)
    assert error.value.entity == "Exam"


def test_card_crud(make_deck, make_card):
    deck = make_deck()
    first = make_card(deck.id, front="A")
    second = make_card(deck.id, front="B")
    assert isinstance(first, CardResponse)
    assert [card.id for card in cards.list_cards_by_deck(deck.id)] == [first.id, second.id]

    updated = cards.update_card(first.id, CardUpdate(back="Neu"))
    assert updated.back == "Neu"
    assert updated.front == "A"

    moved = cards.reposition_card(second.id, 0)
    assert moved.position == 0
    assert [card.id for card in cards.list_cards_by_deck(deck.id)] == [second.id, first.id]

    cards.delete_card(second.id)
    assert cards.get_card(first.id).position == 0


def test_cards_by_exam_and_due(make_exam, make_deck, make_card):
    exam = make_exam()
    deck = make_deck(exam_id=exam.id)
    card = make_card(deck.id)
    assert cards.list_cards_by_exam(exam.id) == [card]
    assert cards.list_cards_by_exam(exam.id, due=True) == [card]
    assert cards.list_cards_by_deck(deck.id, due=True) == [card]


def test_card_unknown_deck(make_card):
    with pytest.raises(NotFoundError) as error:
        make_card(99)
    assert error.value.entity == "Deck"


def test_card_unknown_image(make_deck, make_card):
    deck = make_deck()
    with pytest.raises(NotFoundError) as error:
        make_card(deck.id, front_image="missing.png")
    assert error.value.entity == "Image"


def test_save_and_get_image(started, make_deck, make_card):
    name = images.save_image(b"png", "foto.PNG", "image/png")
    assert name.endswith(".png")
    assert images.get_image_path(name).read_bytes() == b"png"
    card = make_card(make_deck().id, front_image=name)
    assert card.front_image == name


@pytest.mark.parametrize(
    ("filename", "content_type", "extension"),
    [
        ("foto.jpeg", "image/jpeg", ".jpeg"),
        ("foto", "image/png", ".png"),
        ("foto.heic", "application/octet-stream", ".heic"),
        ("foto.txt", "image/png", ".png"),
    ],
)
def test_image_extension(started, filename, content_type, extension):
    assert images.save_image(b"x", filename, content_type).endswith(extension)


def test_invalid_images(started):
    with pytest.raises(InvalidImageError):
        images.save_image(b"", "foto.png", "image/png")
    with pytest.raises(InvalidImageError):
        images.save_image(b"x", None, None)
    with pytest.raises(NotFoundError):
        images.get_image_path("missing.png")


def test_timezone_preserved(make_exam):
    exam = make_exam(exam_date=datetime(2026, 9, 1, 8, 0, tzinfo=timezone.utc))
    assert exams.get_exam(exam.id).exam_date == datetime(2026, 9, 1, 8, 0, tzinfo=timezone.utc)
