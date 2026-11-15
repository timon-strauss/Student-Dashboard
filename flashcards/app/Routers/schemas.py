from enum import IntEnum

from pydantic import AwareDatetime, BaseModel, Field, ValidationInfo, field_validator


def _not_null(value, info: ValidationInfo):
    if value is None:
        raise ValueError(f"{info.field_name} must not be null")
    return value


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


class CardState(IntEnum):
    LEARNING = 1
    REVIEW = 2
    RELEARNING = 3


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


class Rating(IntEnum):
    AGAIN = 1
    HARD = 2
    GOOD = 3
    EASY = 4


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
