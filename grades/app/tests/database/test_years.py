import pytest

from app.Database import NotFoundError
from app.Database.schemas import YearCreate, YearResponse, YearUpdate


def test_create_and_get(db):
    year = db.create_year(YearCreate(year="2025"))

    assert isinstance(year, YearResponse)
    assert year.year == "2025"
    assert db.get_year(year.id) == year


def test_get_missing_raises(db):
    with pytest.raises(NotFoundError) as exc:
        db.get_year(7)

    assert (exc.value.entity, exc.value.entity_id) == ("Year", 7)


def test_create_appends_position(make_year):
    assert [make_year(year=str(n)).position for n in range(3)] == [0, 1, 2]


def test_list_ordered_by_position(make_year, db):
    first = make_year(year="2026")
    second = make_year(year="2025")

    assert db.list_years() == [first, second]


def _order(db):
    return [(y.year, y.position) for y in db.list_years()]


def test_reposition_forward(make_year, db):
    a, b, c = (make_year(year=n) for n in "abc")

    moved = db.reposition_year(a.id, 2)

    assert moved.position == 2
    assert _order(db) == [("b", 0), ("c", 1), ("a", 2)]


def test_reposition_backward(make_year, db):
    a, b, c = (make_year(year=n) for n in "abc")

    db.reposition_year(c.id, 0)

    assert _order(db) == [("c", 0), ("a", 1), ("b", 2)]


def test_reposition_clamps_to_last(make_year, db):
    a, b = (make_year(year=n) for n in "ab")

    assert db.reposition_year(a.id, 99).position == 1
    assert _order(db) == [("b", 0), ("a", 1)]


def test_reposition_same_position(make_year, db):
    a, b = (make_year(year=n) for n in "ab")

    assert db.reposition_year(b.id, 1) == b


def test_reposition_missing_raises(db):
    with pytest.raises(NotFoundError):
        db.reposition_year(1, 0)


def test_delete_closes_position_gap(make_year, db):
    a, b, c = (make_year(year=n) for n in "abc")

    db.delete_year(b.id)

    assert _order(db) == [("a", 0), ("c", 1)]


def test_list_empty(db):
    assert db.list_years() == []


def test_update(make_year, db):
    year = make_year()

    updated = db.update_year(year.id, YearUpdate(year="2026"))

    assert updated.year == "2026"
    assert db.get_year(year.id) == updated


def test_update_empty_keeps_values(make_year, db):
    year = make_year()

    assert db.update_year(year.id, YearUpdate()) == year


def test_update_missing_raises(db):
    with pytest.raises(NotFoundError):
        db.update_year(1, YearUpdate(year="2026"))


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
