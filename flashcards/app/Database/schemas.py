from pydantic import AwareDatetime, BaseModel, ConfigDict, ValidationInfo, field_validator

from schemas import CardState, Rating

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

    @field_validator("name", "exam_date")
    @classmethod
    def not_null(cls, value, info: ValidationInfo):
        if value is None:
            raise ValueError(f"{info.field_name} must not be null")
        return value


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

    @field_validator("name")
    @classmethod
    def not_null(cls, value, info: ValidationInfo):
        if value is None:
            raise ValueError(f"{info.field_name} must not be null")
        return value


class DeckResponse(DeckBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


# --- Card ---


class CardContent(BaseModel):
    front: str
    front_image: str | None = None
    back: str
    back_image: str | None = None


class CardBase(CardContent):
    deck_id: int


class CardCreate(CardBase):
    ...


class CardUpdate(BaseModel):
    front: str | None = None
    front_image: str | None = None
    back: str | None = None
    back_image: str | None = None

    @field_validator("front", "back")
    @classmethod
    def not_null(cls, value, info: ValidationInfo):
        if value is None:
            raise ValueError(f"{info.field_name} must not be null")
        return value


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
    position: int
    created_at: AwareDatetime


# --- Review ---


class ReviewLogCreate(BaseModel):
    rating: Rating
    reviewed_at: AwareDatetime


class ReviewLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    card_id: int
    rating: Rating
    reviewed_at: AwareDatetime


# --- Import ---


class DeckImport(BaseModel):
    name: str
    description: str | None = None
    cards: list[CardContent] = []


class ExamImport(ExamBase):
    decks: list[DeckImport] = []
