from pydantic import BaseModel, Field, ValidationInfo, field_validator, model_validator


def _not_null(value, info: ValidationInfo):
    if value is None:
        raise ValueError(f"{info.field_name} must not be null")
    return value


# --- Year ---


class YearCreate(BaseModel):
    year: str = Field(min_length=1)


class YearUpdate(BaseModel):
    year: str | None = Field(default=None, min_length=1)

    check_required = field_validator("year")(_not_null)


class YearReposition(BaseModel):
    position: int = Field(ge=0)


class YearResponse(BaseModel):
    id: int
    year: str
    position: int


# --- Module ---


class ModuleCreate(BaseModel):
    year_id: int
    name: str = Field(min_length=1)
    grade: float | None = Field(default=None, ge=1.0, le=6.0)
    ects: int = Field(gt=0)
    passed: bool = False


class ModuleUpdate(BaseModel):
    year_id: int | None = None
    name: str | None = Field(default=None, min_length=1)
    grade: float | None = Field(default=None, ge=1.0, le=6.0)
    ects: int | None = Field(default=None, gt=0)
    passed: bool | None = None

    check_required = field_validator("year_id", "name", "ects", "passed")(_not_null)


class ModuleResponse(BaseModel):
    id: int
    year_id: int
    name: str
    grade: float | None
    ects: int
    passed: bool
    grade_from_submodules: bool
    reached_points: float | None
    max_points: float | None


# --- Submodule ---


class SubmoduleCreate(BaseModel):
    module_id: int
    name: str = Field(min_length=1)
    max_points: float = Field(gt=0)
    reached_points: float | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def reached_within_max(self):
        if self.reached_points is not None and self.reached_points > self.max_points:
            raise ValueError("reached_points must not exceed max_points")
        return self


class SubmoduleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    max_points: float | None = Field(default=None, gt=0)
    reached_points: float | None = Field(default=None, ge=0)

    check_required = field_validator("name", "max_points")(_not_null)


class SubmoduleResponse(BaseModel):
    id: int
    module_id: int
    name: str
    max_points: float
    reached_points: float | None


# --- Statistics ---


class GradeSummary(BaseModel):
    grade: float | None
    ects: int
    passed_ects: int


class YearProgress(BaseModel):
    year_id: int
    year: str
    grade: float | None
    ects: int
    cumulative_grade: float | None
    cumulative_ects: int


class ModuleProgress(BaseModel):
    reached_percentage: float | None
    reached_points: float
    graded_max_points: float
    total_max_points: float
