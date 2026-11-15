
from enum import IntEnum

from pydantic import AwareDatetime, BaseModel, ConfigDict

# --- Exam ---

class ExamBase(BaseModel):
    name: str
    description: str | None = None
    exam_date: AwareDatetime


class ExamCreate(ExamBase):
    ...


class ExamUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    exam_date: AwareDatetime | None = None


class ExamResponse(ExamBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


# --- Deck ---


class DeckBase(BaseModel):
    exam_id: int | None = None
    name: str
    description: str | None = None


class DeckCreate(DeckBase):
    ...


class DeckUpdate(BaseModel):
    exam_id: int | None = None
    name: str | None = None
    description: str | None = None


class DeckResponse(DeckBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


# --- Card ---


class CardState(IntEnum):
    LEARNING = 1
    REVIEW = 2
    RELEARNING = 3


class CardBase(BaseModel):
    deck_id: int
    front: str
    front_image: str | None = None
    back: str
    back_image: str | None = None
    position: int = 0


class CardCreate(CardBase):
    ...


class CardUpdate(BaseModel):
    deck_id: int | None = None
    front: str | None = None
    front_image: str | None = None
    back: str | None = None
    back_image: str | None = None
    position: int | None = None


class CardSchedule(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    state: CardState
    step: int | None
    stability: float | None
    difficulty: float | None
    due: AwareDatetime
    last_review: AwareDatetime | None


class CardResponse(CardBase, CardSchedule):
    model_config = ConfigDict(from_attributes=True)

    id: int


# --- Review ---


class Rating(IntEnum):
    AGAIN = 1
    HARD = 2
    GOOD = 3
    EASY = 4


class ReviewCreate(BaseModel):
    rating: Rating
    reviewed_at: AwareDatetime | None = None


class ReviewLogCreate(BaseModel):
    rating: Rating
    reviewed_at: AwareDatetime


class ReviewLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    card_id: int
    rating: Rating
    reviewed_at: AwareDatetime
