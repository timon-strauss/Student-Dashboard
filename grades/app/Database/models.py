from sqlalchemy import CheckConstraint, Float, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Year(Base):
    __tablename__ = "years"
    __table_args__ = (CheckConstraint("year > 0", name="ck_years_year"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    year: Mapped[int]

    modules: Mapped[list["Module"]] = relationship(
        back_populates="year", cascade="all, delete-orphan", passive_deletes=True
    )


class Module(Base):
    __tablename__ = "modules"
    __table_args__ = (
        CheckConstraint("grade IS NULL OR (grade >= 1.0 AND grade <= 6.0)", name="ck_modules_grade"),
        CheckConstraint("ects > 0", name="ck_modules_ects"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    year_id: Mapped[int] = mapped_column(ForeignKey("years.id", ondelete="CASCADE"), index=True)
    name: Mapped[str]
    grade: Mapped[float | None] = mapped_column(Float)
    ects: Mapped[int]
    passed: Mapped[bool] = mapped_column(default=False)

    year: Mapped["Year"] = relationship(back_populates="modules")
    submodules: Mapped[list["Submodule"]] = relationship(
        back_populates="module", cascade="all, delete-orphan", passive_deletes=True
    )


class Submodule(Base):
    __tablename__ = "submodules"
    __table_args__ = (
        CheckConstraint("max_points > 0", name="ck_submodules_max_points"),
        CheckConstraint(
            "reached_points IS NULL OR (reached_points >= 0 AND reached_points <= max_points)",
            name="ck_submodules_reached_points",
        ),
        CheckConstraint("weight > 0", name="ck_submodules_weight"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    module_id: Mapped[int] = mapped_column(ForeignKey("modules.id", ondelete="CASCADE"), index=True)
    name: Mapped[str]
    max_points: Mapped[float] = mapped_column(Float)
    reached_points: Mapped[float | None] = mapped_column(Float)
    weight: Mapped[float] = mapped_column(Float)

    module: Mapped["Module"] = relationship(back_populates="submodules")
