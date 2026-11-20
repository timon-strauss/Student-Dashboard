import pytest

from app.Database import NotFoundError
from app.Database.schemas import YearCreate, YearResponse, YearUpdate


def test_create_and_get(db):
    year = db.create_year(YearCreate(year=2025))

    assert isinstance(year, YearResponse)
    assert year.year == 2025
    assert db.get_year(year.id) == year


def test_get_missing_raises(db):
    with pytest.raises(NotFoundError) as exc:
        db.get_year(7)

    assert (exc.value.entity, exc.value.entity_id) == ("Year", 7)


def test_list_ordered_by_year(make_year, db):
    later = make_year(year=2026)
    earlier = make_year(year=2025)

    assert db.list_years() == [earlier, later]


def test_list_empty(db):
    assert db.list_years() == []


def test_update(make_year, db):
    year = make_year()

    updated = db.update_year(year.id, YearUpdate(year=2026))

    assert updated.year == 2026
    assert db.get_year(year.id) == updated


def test_update_empty_keeps_values(make_year, db):
    year = make_year()

    assert db.update_year(year.id, YearUpdate()) == year


def test_update_missing_raises(db):
    with pytest.raises(NotFoundError):
        db.update_year(1, YearUpdate(year=2026))


def test_delete(make_year, db):
    year = make_year()

    db.delete_year(year.id)

    assert db.list_years() == []


def test_delete_cascades_to_modules_and_submodules(make_year, make_module, make_submodule, db):
    year = make_year()
    module = make_module(year.id)
    submodule = make_submodule(module.id)

    db.delete_year(year.id)

    with pytest.raises(NotFoundError):
        db.get_module(module.id)
    with pytest.raises(NotFoundError):
        db.get_submodule(submodule.id)


def test_delete_missing_raises(db):
    with pytest.raises(NotFoundError):
        db.delete_year(3)
