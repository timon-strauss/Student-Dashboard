from datetime import date

from pydantic import AwareDatetime, BaseModel, Field, ValidationInfo, field_validator

from schemas import CardState, Rating


def _not_null(value, info: ValidationInfo):
    if value is None:
        raise ValueError(f"{info.field_name} must not be null")
    return value


# --- Exam ---


class ExamCreate(BaseModel):
    name: str = Field(min_length=1)
    description: str | None = None
    exam_date: AwareDatetime


class ExamUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    description: str | None = None
    exam_date: AwareDatetime | None = None

    check_required = field_validator("name", "exam_date")(_not_null)


class ExamResponse(BaseModel):
    id: int
    name: str
    description: str | None
    exam_date: AwareDatetime


# --- Deck ---


class DeckCreate(BaseModel):
    exam_id: int | None = None
    name: str = Field(min_length=1)
    description: str | None = None


class DeckUpdate(BaseModel):
    exam_id: int | None = None
    name: str | None = Field(default=None, min_length=1)
    description: str | None = None

    check_required = field_validator("name")(_not_null)


class DeckResponse(BaseModel):
    id: int
    exam_id: int | None
    name: str
    description: str | None


# --- Card ---


class CardCreate(BaseModel):
    deck_id: int
    front: str = Field(min_length=1)
    front_image: str | None = None
    back: str = Field(min_length=1)
    back_image: str | None = None


class CardUpdate(BaseModel):
    deck_id: int | None = None
    front: str | None = Field(default=None, min_length=1)
    front_image: str | None = None
    back: str | None = Field(default=None, min_length=1)
    back_image: str | None = None

    check_required = field_validator("deck_id", "front", "back")(_not_null)


class CardReview(BaseModel):
    rating: Rating


class CardReposition(BaseModel):
    position: int = Field(ge=0)


class CardResponse(BaseModel):
    id: int
    deck_id: int
    front: str
    front_image: str | None
    back: str
    back_image: str | None
    position: int
    state: CardState
    due: AwareDatetime
    last_review: AwareDatetime | None


# --- Statistics ---


class DueCount(BaseModel):
    due: int


class CardStatusCounts(BaseModel):
    due: int
    learned: int
    consolidated: int


class ConsolidatedPoint(BaseModel):
    date: date
    consolidated: int


# --- Transfer ---


class ImageTransfer(BaseModel):
    media_type: str
    data: str = Field(min_length=1, description="Base64 encoded image")


class CardTransfer(BaseModel):
    front: str = Field(min_length=1)
    front_image: ImageTransfer | None = None
    back: str = Field(min_length=1)
    back_image: ImageTransfer | None = None


class DeckTransfer(BaseModel):
    name: str = Field(min_length=1)
    description: str | None = None
    cards: list[CardTransfer] = Field(default_factory=list)


class ExamTransfer(BaseModel):
    name: str = Field(min_length=1)
    description: str | None = None
    exam_date: AwareDatetime
    decks: list[DeckTransfer] = Field(default_factory=list)
