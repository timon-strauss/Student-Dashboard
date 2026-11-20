import pytest

from app.Database import NotFoundError
from app.Database.schemas import ModuleCreate, ModuleResponse, ModuleUpdate


def test_create_and_get(make_year, db):
    year = make_year()

    module = db.create_module(ModuleCreate(year_id=year.id, name="Analysis", grade=1.7, ects=8, passed=True))

    assert isinstance(module, ModuleResponse)
    assert (module.year_id, module.name, module.grade, module.ects, module.passed) == (
        year.id,
        "Analysis",
        1.7,
        8,
        True,
    )
    assert db.get_module(module.id) == module


def test_create_defaults(make_year, make_module):
    module = make_module(make_year().id)

    assert module.grade is None
    assert module.passed is False


def test_create_with_missing_year_raises_and_persists_nothing(make_year, db):
    with pytest.raises(NotFoundError) as exc:
        db.create_module(ModuleCreate(year_id=99, name="x", ects=5))

    assert (exc.value.entity, exc.value.entity_id) == ("Year", 99)
    assert db.list_modules(make_year().id) == []


def test_get_missing_raises(db):
    with pytest.raises(NotFoundError) as exc:
        db.get_module(5)

    assert exc.value.entity == "Module"


def test_list_filters_by_year(make_year, make_module, db):
    year_a = make_year(year=2025)
    year_b = make_year(year=2026)
    a1 = make_module(year_a.id)
    a2 = make_module(year_a.id)
    make_module(year_b.id)

    assert db.list_modules(year_a.id) == [a1, a2]


def test_list_missing_year_raises(db):
    with pytest.raises(NotFoundError):
        db.list_modules(42)


def test_update_partial(make_year, make_module, db):
    module = make_module(make_year().id, name="alt", ects=5)

    updated = db.update_module(module.id, ModuleUpdate(grade=2.3, passed=True))

    assert (updated.name, updated.ects, updated.grade, updated.passed) == ("alt", 5, 2.3, True)
    assert db.get_module(module.id) == updated


def test_update_clears_grade(make_year, make_module, db):
    module = make_module(make_year().id, grade=3.0)

    assert db.update_module(module.id, ModuleUpdate(grade=None)).grade is None


def test_update_moves_to_other_year(make_year, make_module, db):
    old = make_year(year=2025)
    new = make_year(year=2026)
    module = make_module(old.id)

    db.update_module(module.id, ModuleUpdate(year_id=new.id))

    assert db.list_modules(old.id) == []
    assert [m.id for m in db.list_modules(new.id)] == [module.id]


def test_update_to_missing_year_raises_and_keeps_module(make_year, make_module, db):
    module = make_module(make_year().id)

    with pytest.raises(NotFoundError) as exc:
        db.update_module(module.id, ModuleUpdate(year_id=99, name="neu"))

    assert exc.value.entity == "Year"
    assert db.get_module(module.id) == module


def test_update_missing_raises(db):
    with pytest.raises(NotFoundError):
        db.update_module(1, ModuleUpdate(name="x"))


def test_delete_cascades_to_submodules(make_year, make_module, make_submodule, db):
    module = make_module(make_year().id)
    submodule = make_submodule(module.id)

    db.delete_module(module.id)

    with pytest.raises(NotFoundError):
        db.get_module(module.id)
    with pytest.raises(NotFoundError):
        db.get_submodule(submodule.id)


def test_delete_missing_raises(db):
    with pytest.raises(NotFoundError):
        db.delete_module(3)
