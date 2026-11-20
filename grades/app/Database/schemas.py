from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator, model_validator

Grade = Annotated[float, Field(ge=1.0, le=6.0)]
YearLabel = Annotated[str, Field(min_length=1)]
Ects = Annotated[int, Field(gt=0)]
MaxPoints = Annotated[float, Field(gt=0)]
ReachedPoints = Annotated[float, Field(ge=0)]
Weight = Annotated[float, Field(gt=0)]

# --- Year ---


class YearBase(BaseModel):
    year: YearLabel


class YearCreate(YearBase):
    ...


class YearUpdate(BaseModel):
    year: YearLabel | None = None

    @field_validator("year")
    @classmethod
    def not_null(cls, value, info: ValidationInfo):
        if value is None:
            raise ValueError(f"{info.field_name} must not be null")
        return value


class YearResponse(YearBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


# --- Module ---


class ModuleBase(BaseModel):
    year_id: int
    name: str
    grade: Grade | None = None
    ects: Ects
    passed: bool = False


class ModuleCreate(ModuleBase):
    ...


class ModuleUpdate(BaseModel):
    year_id: int | None = None
    name: str | None = None
    grade: Grade | None = None
    ects: Ects | None = None
    passed: bool | None = None

    @field_validator("year_id", "name", "ects", "passed")
    @classmethod
    def not_null(cls, value, info: ValidationInfo):
        if value is None:
            raise ValueError(f"{info.field_name} must not be null")
        return value


class ModuleResponse(ModuleBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


# --- Submodule ---


class SubmoduleBase(BaseModel):
    module_id: int
    name: str
    max_points: MaxPoints
    reached_points: ReachedPoints | None = None
    weight: Weight

    @model_validator(mode="after")
    def reached_within_max(self):
        if self.reached_points is not None and self.reached_points > self.max_points:
            raise ValueError("reached_points must not exceed max_points")
        return self


class SubmoduleCreate(SubmoduleBase):
    ...


class SubmoduleUpdate(BaseModel):
    name: str | None = None
    max_points: MaxPoints | None = None
    reached_points: ReachedPoints | None = None
    weight: Weight | None = None

    @field_validator("name", "max_points", "weight")
    @classmethod
    def not_null(cls, value, info: ValidationInfo):
        if value is None:
            raise ValueError(f"{info.field_name} must not be null")
        return value


class SubmoduleResponse(SubmoduleBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
