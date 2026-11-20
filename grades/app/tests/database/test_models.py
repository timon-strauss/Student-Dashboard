import pytest
from sqlalchemy.exc import IntegrityError

from app.Database.models import Module, Submodule, Year


@pytest.fixture
def session(db):
    with db._session() as session:
        yield session


@pytest.fixture
def module(session):
    year = Year(year="2025")
    session.add(year)
    session.flush()
    module = Module(year_id=year.id, name="m", ects=5)
    session.add(module)
    session.flush()
    return module


def test_year_constraint_rejects_empty(session):
    session.add(Year(year=""))

    with pytest.raises(IntegrityError):
        session.flush()


@pytest.mark.parametrize("grade", [0.5, 6.5])
def test_module_grade_constraint(session, module, grade):
    module.grade = grade

    with pytest.raises(IntegrityError):
        session.flush()


def test_module_ects_constraint(session, module):
    module.ects = 0

    with pytest.raises(IntegrityError):
        session.flush()


def test_module_requires_existing_year(session):
    session.add(Module(year_id=99, name="m", ects=5))

    with pytest.raises(IntegrityError):
        session.flush()


@pytest.mark.parametrize(
    "values",
    [
        {"max_points": 0, "weight": 1},
        {"max_points": 10, "weight": 0},
        {"max_points": 10, "weight": 1, "reached_points": -1},
        {"max_points": 10, "weight": 1, "reached_points": 11},
    ],
)
def test_submodule_constraints(session, module, values):
    session.add(Submodule(module_id=module.id, name="s", **values))

    with pytest.raises(IntegrityError):
        session.flush()


def test_submodule_requires_existing_module(session):
    session.add(Submodule(module_id=99, name="s", max_points=10, weight=1))

    with pytest.raises(IntegrityError):
        session.flush()
