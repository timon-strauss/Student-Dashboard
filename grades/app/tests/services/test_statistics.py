import pytest


@pytest.fixture
def year(client):
    def _make(label):
        return client.post("/api/years", json={"year": label}).json()["id"]

    return _make


@pytest.fixture
def module(client):
    def _make(year_id, ects, grade=None, passed=False):
        body = {"year_id": year_id, "name": "m", "ects": ects, "grade": grade, "passed": passed}
        return client.post("/api/modules", json=body).json()["id"]

    return _make


@pytest.fixture
def submodule(client):
    def _make(module_id, max_points, weight, reached_points=None):
        body = {
            "module_id": module_id,
            "name": "s",
            "max_points": max_points,
            "weight": weight,
            "reached_points": reached_points,
        }
        return client.post("/api/submodules", json=body).json()["id"]

    return _make


def test_overall_without_modules(client):
    assert client.get("/api/statistics/overall").json() == {"grade": None, "ects": 0}


def test_overall_is_ects_weighted(client, year, module):
    first = year("a")
    second = year("b")
    module(first, ects=10, grade=1.0)
    module(second, ects=5, grade=2.5)

    assert client.get("/api/statistics/overall").json() == {"grade": 1.5, "ects": 15}


def test_ungraded_or_failed_modules_are_ignored_for_grade(client, year, module):
    year_id = year("a")
    module(year_id, ects=5, grade=2.0)
    module(year_id, ects=5, grade=None, passed=True)
    module(year_id, ects=5, grade=5.0, passed=False)

    assert client.get(f"/api/statistics/years/{year_id}").json() == {"grade": 2.0, "ects": 5}


def test_year_grade(client, year, module):
    first = year("a")
    second = year("b")
    module(first, ects=6, grade=1.3)
    module(first, ects=3, grade=2.3)
    module(second, ects=5, grade=4.0)

    assert client.get(f"/api/statistics/years/{first}").json() == {"grade": 1.63, "ects": 9}


def test_year_grade_missing_year(client):
    assert client.get("/api/statistics/years/9").status_code == 404


def test_progression_follows_year_order(client, year, module):
    first = year("a")
    second = year("b")
    third = year("c")
    module(first, ects=10, grade=1.0)
    module(second, ects=10, grade=3.0)
    client.put(f"/api/years/{second}/position", json={"position": 0})

    assert client.get("/api/statistics/progression").json() == [
        {"year_id": second, "year": "b", "grade": 3.0, "ects": 10, "cumulative_grade": 3.0, "cumulative_ects": 10},
        {"year_id": first, "year": "a", "grade": 1.0, "ects": 10, "cumulative_grade": 2.0, "cumulative_ects": 20},
        {"year_id": third, "year": "c", "grade": None, "ects": 0, "cumulative_grade": 2.0, "cumulative_ects": 20},
    ]


def test_progression_empty(client):
    assert client.get("/api/statistics/progression").json() == []


def test_module_progress_weighted(client, year, module, submodule):
    module_id = module(year("a"), ects=5)
    submodule(module_id, max_points=100, weight=3, reached_points=80)
    submodule(module_id, max_points=60, weight=1, reached_points=30)
    submodule(module_id, max_points=90, weight=2)

    assert client.get(f"/api/statistics/modules/{module_id}").json() == {
        "reached_percentage": 72.5,
        "graded_weight": 4.0,
        "total_weight": 6.0,
    }


def test_module_progress_without_points(client, year, module, submodule):
    module_id = module(year("a"), ects=5)
    submodule(module_id, max_points=100, weight=1)

    assert client.get(f"/api/statistics/modules/{module_id}").json() == {
        "reached_percentage": None,
        "graded_weight": 0.0,
        "total_weight": 1.0,
    }


def test_module_progress_missing_module(client):
    assert client.get("/api/statistics/modules/9").status_code == 404


def test_calculated_grade_used_when_no_grade_entered(client, year, module, submodule):
    year_id = year("a")
    calculated = module(year_id, ects=10)
    submodule(calculated, max_points=100, weight=1, reached_points=50)
    module(year_id, ects=10, grade=2.0)

    assert client.get(f"/api/statistics/years/{year_id}").json() == {"grade": 3.0, "ects": 20}


def test_incomplete_submodules_do_not_count(client, year, module, submodule):
    module_id = module(year("a"), ects=5)
    submodule(module_id, max_points=100, weight=1, reached_points=100)
    submodule(module_id, max_points=100, weight=1)

    assert client.get("/api/statistics/overall").json() == {"grade": None, "ects": 0}


def test_failed_calculated_grade_does_not_count(client, year, module, submodule):
    module_id = module(year("a"), ects=5)
    submodule(module_id, max_points=100, weight=1, reached_points=0)

    assert client.get("/api/statistics/overall").json() == {"grade": None, "ects": 0}


def test_failed_entered_grade_does_not_count(client, year, module):
    module(year("a"), ects=5, grade=4.3)

    assert client.get("/api/statistics/overall").json() == {"grade": None, "ects": 0}


def test_progression_uses_calculated_grades(client, year, module, submodule):
    first = year("a")
    module_id = module(first, ects=5)
    submodule(module_id, max_points=60, weight=1, reached_points=59.5)

    assert client.get("/api/statistics/progression").json()[0]["grade"] == 1.0


def test_formula_sums_grade_times_ects_over_accounted_ects(client, year, module, submodule):
    first = year("a")
    second = year("b")
    module(first, ects=5, grade=1.0)
    module(first, ects=10, grade=2.0)
    module(first, ects=30, passed=True)
    module(first, ects=8)
    module(second, ects=15, grade=4.3)
    calculated = module(second, ects=10)
    submodule(calculated, max_points=100, weight=1, reached_points=50)
    incomplete = module(second, ects=20)
    submodule(incomplete, max_points=100, weight=1, reached_points=100)
    submodule(incomplete, max_points=100, weight=1)

    assert client.get("/api/statistics/overall").json() == {"grade": 2.6, "ects": 25}
    assert client.get(f"/api/statistics/years/{first}").json() == {"grade": 1.67, "ects": 15}
    assert client.get(f"/api/statistics/years/{second}").json() == {"grade": 4.0, "ects": 10}
    assert client.get("/api/statistics/progression").json() == [
        {"year_id": first, "year": "a", "grade": 1.67, "ects": 15, "cumulative_grade": 1.67, "cumulative_ects": 15},
        {"year_id": second, "year": "b", "grade": 4.0, "ects": 10, "cumulative_grade": 2.6, "cumulative_ects": 25},
    ]


def test_only_ungraded_modules_give_empty_statistics(client, year, module):
    year_id = year("a")
    module(year_id, ects=30, passed=True)
    module(year_id, ects=5)

    assert client.get("/api/statistics/overall").json() == {"grade": None, "ects": 0}
    assert client.get("/api/statistics/progression").json()[0]["cumulative_ects"] == 0
