from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from Database.models import Card, Deck, Exam
from Database.schemas import (
    CardCreate,
    CardResponse,
    CardSchedule,
    CardState,
    CardUpdate,
    DeckCreate,
    DeckResponse,
    DeckUpdate,
    ExamCreate,
    ExamResponse,
    ExamUpdate,
    Rating,
    ReviewLogCreate,
)

AWARE = datetime(2026, 1, 1, tzinfo=timezone.utc)
NAIVE = datetime(2026, 1, 1)


class TestExamSchemas:
    def test_create_defaults_description_to_none(self):
        exam = ExamCreate(name="Mathe", exam_date=AWARE)

        assert exam.description is None

    def test_create_rejects_naive_datetime(self):
        with pytest.raises(ValidationError):
            ExamCreate(name="Mathe", exam_date=NAIVE)

    def test_create_requires_name_and_date(self):
        with pytest.raises(ValidationError):
            ExamCreate()

    def test_update_tracks_only_set_fields(self):
        update = ExamUpdate(name="Neu")

        assert update.model_dump(exclude_unset=True) == {"name": "Neu"}

    @pytest.mark.parametrize("field", ["name", "exam_date"])
    def test_update_rejects_explicit_null_for_required_fields(self, field):
        with pytest.raises(ValidationError, match=f"{field} must not be null"):
            ExamUpdate(**{field: None})

    def test_update_allows_clearing_description(self):
        update = ExamUpdate(description=None)

        assert update.model_dump(exclude_unset=True) == {"description": None}

    def test_update_rejects_naive_datetime(self):
        with pytest.raises(ValidationError):
            ExamUpdate(exam_date=NAIVE)

    def test_response_from_orm_object(self):
        exam = Exam(id=1, name="Mathe", description=None, exam_date=AWARE)

        response = ExamResponse.model_validate(exam)

        assert response == ExamResponse(id=1, name="Mathe", exam_date=AWARE)


class TestDeckSchemas:
    def test_create_exam_id_is_optional(self):
        assert DeckCreate(name="Deck").exam_id is None

    def test_update_rejects_null_name(self):
        with pytest.raises(ValidationError, match="name must not be null"):
            DeckUpdate(name=None)

    def test_update_allows_null_exam_id_to_detach(self):
        update = DeckUpdate(exam_id=None)

        assert update.model_dump(exclude_unset=True) == {"exam_id": None}

    def test_response_from_orm_object(self):
        deck = Deck(id=3, exam_id=None, name="Deck", description="d")

        assert DeckResponse.model_validate(deck).model_dump() == {
            "id": 3,
            "exam_id": None,
            "name": "Deck",
            "description": "d",
        }


class TestCardSchemas:
    def test_create_defaults(self):
        card = CardCreate(deck_id=1, front="f", back="b")

        assert "position" not in CardCreate.model_fields
        assert card.front_image is None
        assert card.back_image is None

    @pytest.mark.parametrize("field", ["front", "back"])
    def test_update_rejects_null_for_required_fields(self, field):
        with pytest.raises(ValidationError, match=f"{field} must not be null"):
            CardUpdate(**{field: None})

    @pytest.mark.parametrize("field", ["front_image", "back_image"])
    def test_update_allows_clearing_images(self, field):
        assert CardUpdate(**{field: None}).model_dump(exclude_unset=True) == {field: None}

    def test_schedule_validates_state(self):
        with pytest.raises(ValidationError):
            CardSchedule(
                state=4, step=None, stability=None, difficulty=None, due=AWARE, last_review=None
            )

    def test_schedule_coerces_state_to_enum(self):
        schedule = CardSchedule(
            state=2, step=None, stability=1.0, difficulty=5.0, due=AWARE, last_review=AWARE
        )

        assert schedule.state is CardState.REVIEW

    def test_schedule_rejects_naive_due(self):
        with pytest.raises(ValidationError):
            CardSchedule(
                state=1, step=0, stability=None, difficulty=None, due=NAIVE, last_review=None
            )

    def test_response_from_orm_object(self):
        card = Card(
            id=7,
            deck_id=1,
            front="f",
            front_image=None,
            back="b",
            back_image=None,
            position=2,
            state=1,
            step=0,
            stability=None,
            difficulty=None,
            due=AWARE,
            last_review=None,
            created_at=AWARE,
        )

        response = CardResponse.model_validate(card)

        assert response.id == 7
        assert response.state is CardState.LEARNING
        assert response.position == 2
        assert response.created_at == AWARE

    def test_update_has_no_deck_or_position(self):
        assert {"deck_id", "position"}.isdisjoint(CardUpdate.model_fields)


class TestReviewSchemas:
    @pytest.mark.parametrize("rating", [0, 5])
    def test_create_rejects_invalid_rating(self, rating):
        with pytest.raises(ValidationError):
            ReviewLogCreate(rating=rating, reviewed_at=AWARE)

    def test_create_coerces_rating(self):
        assert ReviewLogCreate(rating=3, reviewed_at=AWARE).rating is Rating.GOOD

    def test_create_rejects_naive_datetime(self):
        with pytest.raises(ValidationError):
            ReviewLogCreate(rating=3, reviewed_at=NAIVE)


def test_enums_match_fsrs_values():
    import fsrs

    assert {s.name.upper(): s.value for s in fsrs.State} == {
        s.name: s.value for s in CardState
    }
    assert {r.name.upper(): r.value for r in fsrs.Rating} == {
        r.name: r.value for r in Rating
    }
