import pytest
from pydantic import ValidationError

from app.Database.models import Module, Submodule, Year
from app.Database.schemas import (
    ModuleCreate,
    ModuleResponse,
    ModuleUpdate,
    SubmoduleCreate,
    SubmoduleResponse,
    SubmoduleUpdate,
    YearCreate,
    YearResponse,
    YearUpdate,
)


class TestYearSchemas:
    def test_create_requires_year(self):
        with pytest.raises(ValidationError):
            YearCreate()

    @pytest.mark.parametrize("year", ["", 2025, None])
    def test_create_rejects_empty_or_non_string_year(self, year):
        with pytest.raises(ValidationError):
            YearCreate(year=year)

    def test_update_rejects_null_year(self):
        with pytest.raises(ValidationError):
            YearUpdate(year=None)

    def test_update_unset_is_empty(self):
        assert YearUpdate().model_dump(exclude_unset=True) == {}

    def test_response_from_orm(self):
        assert YearResponse.model_validate(Year(id=1, year="2025", position=0)) == YearResponse(id=1, year="2025", position=0)


class TestModuleSchemas:
    @pytest.mark.parametrize("grade", [1.0, 2.3, 4.0, 6.0])
    def test_create_accepts_grade_in_range(self, grade):
        assert ModuleCreate(year_id=1, name="m", ects=5, grade=grade).grade == grade

    @pytest.mark.parametrize("grade", [0.9, 6.1, -1])
    def test_create_rejects_grade_out_of_range(self, grade):
        with pytest.raises(ValidationError):
            ModuleCreate(year_id=1, name="m", ects=5, grade=grade)

    @pytest.mark.parametrize("ects", [0, -5, 7.5])
    def test_create_rejects_non_positive_ects(self, ects):
        with pytest.raises(ValidationError):
            ModuleCreate(year_id=1, name="m", ects=ects)

    def test_create_requires_year_name_ects(self):
        with pytest.raises(ValidationError):
            ModuleCreate()

    @pytest.mark.parametrize("field", ["year_id", "name", "ects", "passed"])
    def test_update_rejects_null(self, field):
        with pytest.raises(ValidationError):
            ModuleUpdate(**{field: None})

    def test_update_allows_null_grade(self):
        assert ModuleUpdate(grade=None).model_dump(exclude_unset=True) == {"grade": None}

    def test_update_rejects_grade_out_of_range(self):
        with pytest.raises(ValidationError):
            ModuleUpdate(grade=7)

    def test_response_from_orm(self):
        module = Module(id=2, year_id=1, name="m", grade=1.3, ects=5, passed=True)

        assert ModuleResponse.model_validate(module).grade == 1.3


class TestSubmoduleSchemas:
    def test_create_rejects_reached_above_max(self):
        with pytest.raises(ValidationError, match="must not exceed"):
            SubmoduleCreate(module_id=1, name="s", max_points=10, reached_points=11)

    def test_create_accepts_reached_equal_max(self):
        assert SubmoduleCreate(module_id=1, name="s", max_points=10, reached_points=10).reached_points == 10

    @pytest.mark.parametrize(
        "field, value", [("max_points", 0), ("max_points", -1), ("reached_points", -1)]
    )
    def test_create_rejects_invalid_numbers(self, field, value):
        values = {"module_id": 1, "name": "s", "max_points": 10, field: value}

        with pytest.raises(ValidationError):
            SubmoduleCreate(**values)

    @pytest.mark.parametrize("field", ["name", "max_points"])
    def test_update_rejects_null(self, field):
        with pytest.raises(ValidationError):
            SubmoduleUpdate(**{field: None})

    def test_update_allows_null_reached_points(self):
        assert SubmoduleUpdate(reached_points=None).model_dump(exclude_unset=True) == {"reached_points": None}

    def test_response_from_orm(self):
        submodule = Submodule(id=3, module_id=1, name="s", max_points=10, reached_points=5)

        assert SubmoduleResponse.model_validate(submodule).reached_points == 5
