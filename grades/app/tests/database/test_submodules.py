import pytest

from app.Database import InvalidDataError, NotFoundError
from app.Database.schemas import SubmoduleCreate, SubmoduleResponse, SubmoduleUpdate


@pytest.fixture
def module(make_year, make_module):
    return make_module(make_year().id)


def test_create_and_get(module, db):
    submodule = db.create_submodule(
        SubmoduleCreate(module_id=module.id, name="Klausur", max_points=90, reached_points=72.5, weight=0.7)
    )

    assert isinstance(submodule, SubmoduleResponse)
    assert (submodule.module_id, submodule.name, submodule.max_points, submodule.reached_points, submodule.weight) == (
        module.id,
        "Klausur",
        90,
        72.5,
        0.7,
    )
    assert db.get_submodule(submodule.id) == submodule


def test_create_defaults_reached_points_to_none(module, make_submodule):
    assert make_submodule(module.id).reached_points is None


def test_create_with_missing_module_raises_and_persists_nothing(module, db):
    with pytest.raises(NotFoundError) as exc:
        db.create_submodule(SubmoduleCreate(module_id=99, name="x", max_points=10, weight=1))

    assert (exc.value.entity, exc.value.entity_id) == ("Module", 99)
    assert db.list_submodules(module.id) == []


def test_get_missing_raises(db):
    with pytest.raises(NotFoundError) as exc:
        db.get_submodule(5)

    assert exc.value.entity == "Submodule"


def test_list_filters_by_module(make_year, make_module, make_submodule, db):
    year = make_year()
    module_a = make_module(year.id)
    module_b = make_module(year.id)
    a1 = make_submodule(module_a.id)
    a2 = make_submodule(module_a.id)
    make_submodule(module_b.id)

    assert db.list_submodules(module_a.id) == [a1, a2]


def test_list_all_grouped_by_module(make_year, make_module, make_submodule, db):
    year = make_year()
    module_a = make_module(year.id)
    module_b = make_module(year.id)
    b1 = make_submodule(module_b.id)
    a1 = make_submodule(module_a.id)
    b2 = make_submodule(module_b.id)

    assert db.list_all_submodules() == [a1, b1, b2]


def test_list_all_empty(db):
    assert db.list_all_submodules() == []


def test_list_missing_module_raises(db):
    with pytest.raises(NotFoundError):
        db.list_submodules(42)


def test_update_partial(module, make_submodule, db):
    submodule = make_submodule(module.id, name="Übung", max_points=20, weight=0.3)

    updated = db.update_submodule(submodule.id, SubmoduleUpdate(reached_points=18))

    assert (updated.name, updated.max_points, updated.reached_points, updated.weight) == ("Übung", 20, 18, 0.3)
    assert db.get_submodule(submodule.id) == updated


def test_update_clears_reached_points(module, make_submodule, db):
    submodule = make_submodule(module.id, reached_points=50)

    assert db.update_submodule(submodule.id, SubmoduleUpdate(reached_points=None)).reached_points is None


def test_update_reached_above_stored_max_raises_and_keeps_values(module, make_submodule, db):
    submodule = make_submodule(module.id, max_points=20)

    with pytest.raises(InvalidDataError, match="must not exceed"):
        db.update_submodule(submodule.id, SubmoduleUpdate(reached_points=25))

    assert db.get_submodule(submodule.id) == submodule


def test_update_max_below_stored_reached_raises(module, make_submodule, db):
    submodule = make_submodule(module.id, max_points=20, reached_points=15)

    with pytest.raises(InvalidDataError):
        db.update_submodule(submodule.id, SubmoduleUpdate(max_points=10))

    assert db.get_submodule(submodule.id) == submodule


def test_update_max_and_reached_together(module, make_submodule, db):
    submodule = make_submodule(module.id, max_points=20, reached_points=15)

    updated = db.update_submodule(submodule.id, SubmoduleUpdate(max_points=10, reached_points=8))

    assert (updated.max_points, updated.reached_points) == (10, 8)


def test_update_missing_raises(db):
    with pytest.raises(NotFoundError):
        db.update_submodule(1, SubmoduleUpdate(name="x"))


def test_delete(module, make_submodule, db):
    submodule = make_submodule(module.id)

    db.delete_submodule(submodule.id)

    assert db.list_submodules(module.id) == []


def test_delete_missing_raises(db):
    with pytest.raises(NotFoundError):
        db.delete_submodule(3)
