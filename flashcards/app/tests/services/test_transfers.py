import base64
from datetime import datetime, timezone

import pytest

from Database import db
from Routers.schemas import CardTransfer, DeckTransfer, ExamTransfer, ImageTransfer
from schemas import CardState, Rating
from Services import InvalidImageError, NotFoundError, cards, decks, exams, images, transfers

EXAM_DATE = datetime(2026, 12, 1, 9, 0, tzinfo=timezone.utc)
PNG = ImageTransfer(media_type="image/png", data=base64.b64encode(b"png-bytes").decode())


def uploads(started):
    return sorted(path.name for path in (started / "uploads").iterdir())


def test_export_exam(make_exam, make_deck, make_card, started):
    exam = make_exam(exam_date=EXAM_DATE, description="Analysis")
    deck = make_deck(exam_id=exam.id, name="Kapitel 1")
    image = images.save_image(b"png-bytes", "foto.png", "image/png")
    first = make_card(deck.id, front="A", back="a", front_image=image)
    make_card(deck.id, front="B", back="b")
    cards.reposition_card(first.id, 1)
    make_deck(name="Lose")

    exported = transfers.export_exam(exam.id)
    assert exported.name == "Mathe"
    assert exported.description == "Analysis"
    assert exported.exam_date == EXAM_DATE
    assert [deck.name for deck in exported.decks] == ["Kapitel 1"]
    assert [card.front for card in exported.decks[0].cards] == ["B", "A"]
    assert exported.decks[0].cards[1].front_image == PNG
    assert exported.decks[0].cards[1].back_image is None


def test_export_deck_skips_missing_image_file(make_deck, make_card, started):
    deck = make_deck()
    image = images.save_image(b"png-bytes", "foto.png", "image/png")
    make_card(deck.id, front_image=image)
    (started / "uploads" / image).unlink()
    assert transfers.export_deck(deck.id).cards[0].front_image is None


def test_export_not_found(started):
    with pytest.raises(NotFoundError):
        transfers.export_exam(1)
    with pytest.raises(NotFoundError):
        transfers.export_deck(1)


def test_import_exam(started):
    data = ExamTransfer(
        name="Physik",
        exam_date=EXAM_DATE,
        decks=[
            DeckTransfer(name="Mechanik", cards=[
                CardTransfer(front="F", back="ma", back_image=PNG),
                CardTransfer(front="v", back="s/t"),
            ]),
            DeckTransfer(name="Optik"),
        ],
    )
    exam = transfers.import_exam(data)
    assert exams.get_exam(exam.id) == exam
    imported_decks = decks.list_decks(exam.id)
    assert [deck.name for deck in imported_decks] == ["Mechanik", "Optik"]

    imported_cards = cards.list_cards_by_deck(imported_decks[0].id)
    assert [card.front for card in imported_cards] == ["F", "v"]
    assert [card.position for card in imported_cards] == [0, 1]
    assert all(card.state == CardState.LEARNING and card.last_review is None for card in imported_cards)
    assert images.get_image_path(imported_cards[0].back_image).read_bytes() == b"png-bytes"


def test_import_deck_into_exam_and_standalone(make_exam):
    exam = make_exam()
    data = DeckTransfer(name="Deck", cards=[CardTransfer(front="A", back="a")])
    into_exam = transfers.import_deck(data, exam.id)
    assert into_exam.exam_id == exam.id
    standalone = transfers.import_deck(data, None)
    assert standalone.exam_id is None
    assert decks.list_decks(None) == [standalone]


def test_import_deck_unknown_exam_saves_no_images(started):
    data = DeckTransfer(name="Deck", cards=[CardTransfer(front="A", back="a", front_image=PNG)])
    with pytest.raises(NotFoundError):
        transfers.import_deck(data, 99)
    assert uploads(started) == []


@pytest.mark.parametrize(
    "image",
    [
        ImageTransfer(media_type="image/png", data="not base64!"),
        ImageTransfer(media_type="text/plain", data=base64.b64encode(b"x").decode()),
        ImageTransfer(media_type="image/png", data="===="),
    ],
)
def test_import_invalid_image_saves_nothing(started, image):
    data = DeckTransfer(name="Deck", cards=[
        CardTransfer(front="A", back="a", front_image=PNG),
        CardTransfer(front="B", back="b", back_image=image),
    ])
    with pytest.raises(InvalidImageError):
        transfers.import_deck(data, None)
    assert uploads(started) == []
    assert decks.list_decks(None) == []


def test_roundtrip_resets_learning_progress(make_exam, make_deck, make_card, started):
    exam = make_exam(exam_date=EXAM_DATE)
    deck = make_deck(exam_id=exam.id)
    image = images.save_image(b"png-bytes", "foto.png", "image/png")
    card = make_card(deck.id, front_image=image)
    cards.review_card(card.id, Rating.EASY)

    exported = transfers.export_exam(exam.id)
    copy = transfers.import_exam(exported)
    assert transfers.export_exam(copy.id) == exported
    copied_card = cards.list_cards_by_exam(copy.id)[0]
    assert copied_card.last_review is None
    assert copied_card.front_image != image
    assert db.list_review_logs(copied_card.id) == []


def test_transfer_endpoints(client):
    exam = client.post("/api/exams", json={"name": "Mathe", "exam_date": "2026-12-01T09:00:00+00:00"}).json()
    deck = client.post("/api/decks", json={"exam_id": exam["id"], "name": "Deck"}).json()
    client.post("/api/cards", json={"deck_id": deck["id"], "front": "A", "back": "a"})

    exported = client.get(f"/api/transfer/exams/{exam['id']}")
    assert exported.status_code == 200
    assert exported.json()["decks"][0]["cards"][0]["front"] == "A"
    exported_deck = client.get(f"/api/transfer/decks/{deck['id']}").json()
    assert exported_deck["name"] == "Deck"

    imported = client.post("/api/transfer/exams", json=exported.json())
    assert imported.status_code == 201
    assert imported.json()["name"] == "Mathe"
    imported_deck = client.post("/api/transfer/decks", params={"exam_id": exam["id"]}, json=exported_deck)
    assert imported_deck.status_code == 201
    assert imported_deck.json()["exam_id"] == exam["id"]

    assert client.get("/api/transfer/exams/999").status_code == 404
    assert client.post("/api/transfer/decks", params={"exam_id": 999}, json=exported_deck).status_code == 404
    bad = {"name": "Deck", "cards": [{"front": "A", "back": "a", "front_image": {"media_type": "image/png", "data": "!!"}}]}
    assert client.post("/api/transfer/decks", json=bad).status_code == 415
