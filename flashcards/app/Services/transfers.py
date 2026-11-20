import base64
import binascii

from app.Database import db
from app.Database import schemas as db_schemas
from app.Routers.schemas import CardTransfer, DeckResponse, DeckTransfer, ExamResponse, ExamTransfer, ImageTransfer

from . import images
from ._errors import translate_errors
from .exceptions import InvalidImageError


def _encode_image(name: str | None) -> ImageTransfer | None:
    if name is None:
        return None
    image = images.read_image(name)
    if image is None:
        return None
    data, media_type = image
    return ImageTransfer(media_type=media_type, data=base64.b64encode(data).decode("ascii"))


def _export_deck(deck: db_schemas.DeckResponse) -> DeckTransfer:
    cards = [
        CardTransfer(
            front=card.front,
            front_image=_encode_image(card.front_image),
            back=card.back,
            back_image=_encode_image(card.back_image),
        )
        for card in db.list_cards(deck.id)
    ]
    return DeckTransfer(name=deck.name, description=deck.description, cards=cards)


def _decode_image(image: ImageTransfer) -> bytes:
    try:
        data = base64.b64decode(image.data, validate=True)
    except binascii.Error as error:
        raise InvalidImageError("Image data is not valid base64") from error
    if not data:
        raise InvalidImageError("Image is empty")
    images.extension_for(image.media_type)
    return data


def _validate_images(decks: list[DeckTransfer]) -> None:
    for deck in decks:
        for card in deck.cards:
            for image in (card.front_image, card.back_image):
                if image is not None:
                    _decode_image(image)


def _save_image(image: ImageTransfer | None) -> str | None:
    if image is None:
        return None
    return images.save_image(_decode_image(image), None, image.media_type)


def _deck_import(deck: DeckTransfer) -> db_schemas.DeckImport:
    cards = [
        db_schemas.CardContent(
            front=card.front,
            front_image=_save_image(card.front_image),
            back=card.back,
            back_image=_save_image(card.back_image),
        )
        for card in deck.cards
    ]
    return db_schemas.DeckImport(name=deck.name, description=deck.description, cards=cards)


@translate_errors
def export_exam(exam_id: int) -> ExamTransfer:
    exam = db.get_exam(exam_id)
    return ExamTransfer(
        name=exam.name,
        description=exam.description,
        exam_date=exam.exam_date,
        decks=[_export_deck(deck) for deck in db.list_decks(exam_id)],
    )


@translate_errors
def export_deck(deck_id: int) -> DeckTransfer:
    return _export_deck(db.get_deck(deck_id))


@translate_errors
def import_exam(data: ExamTransfer) -> ExamResponse:
    _validate_images(data.decks)
    exam = db_schemas.ExamImport(
        name=data.name,
        description=data.description,
        exam_date=data.exam_date,
        decks=[_deck_import(deck) for deck in data.decks],
    )
    return ExamResponse.model_validate(db.import_exam(exam).model_dump())


@translate_errors
def import_deck(data: DeckTransfer, exam_id: int | None) -> DeckResponse:
    if exam_id is not None:
        db.get_exam(exam_id)
    _validate_images([data])
    return DeckResponse.model_validate(db.import_deck(_deck_import(data), exam_id).model_dump())
