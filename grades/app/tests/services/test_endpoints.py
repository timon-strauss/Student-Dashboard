def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_year_endpoints(client):
    created = client.post("/api/years", json={"year": "2025/26"})
    assert created.status_code == 201
    assert set(created.json()) == {"id", "year", "position"}
    year_id = created.json()["id"]
    second = client.post("/api/years", json={"year": "2026/27"}).json()

    assert client.get("/api/years").json() == [created.json(), second]
    assert client.get(f"/api/years/{year_id}").json() == created.json()
    assert client.patch(f"/api/years/{year_id}", json={"year": "WS25"}).json()["year"] == "WS25"

    moved = client.put(f"/api/years/{second['id']}/position", json={"position": 0})
    assert moved.json()["position"] == 0
    assert [y["id"] for y in client.get("/api/years").json()] == [second["id"], year_id]

    assert client.delete(f"/api/years/{year_id}").status_code == 204
    missing = client.get(f"/api/years/{year_id}")
    assert missing.status_code == 404
    assert missing.json() == {"detail": f"Year with id {year_id} not found"}


def test_year_validation(client):
    assert client.post("/api/years", json={"year": ""}).status_code == 422
    year_id = client.post("/api/years", json={"year": "2025"}).json()["id"]
    assert client.patch(f"/api/years/{year_id}", json={"year": None}).status_code == 422
    assert client.put(f"/api/years/{year_id}/position", json={"position": -1}).status_code == 422


def test_module_endpoints(client):
    year_a = client.post("/api/years", json={"year": "a"}).json()["id"]
    year_b = client.post("/api/years", json={"year": "b"}).json()["id"]

    created = client.post("/api/modules", json={"year_id": year_a, "name": "Analysis", "ects": 8})
    assert created.status_code == 201
    module = created.json()
    assert module == {
        "id": module["id"],
        "year_id": year_a,
        "name": "Analysis",
        "grade": None,
        "ects": 8,
        "passed": False,
        "grade_from_submodules": False,
    }
    other = client.post("/api/modules", json={"year_id": year_b, "name": "LinA", "ects": 5}).json()

    assert client.get("/api/modules", params={"year_id": year_a}).json() == [module]
    assert client.get("/api/modules").json() == [module, other]

    patched = client.patch(f"/api/modules/{module['id']}", json={"grade": 1.7})
    assert (patched.json()["grade"], patched.json()["passed"]) == (1.7, True)
    assert client.patch(f"/api/modules/{module['id']}", json={"year_id": 99}).status_code == 404

    assert client.delete(f"/api/modules/{module['id']}").status_code == 204
    assert client.get(f"/api/modules/{module['id']}").status_code == 404


def test_module_validation(client):
    year_id = client.post("/api/years", json={"year": "a"}).json()["id"]
    base = {"year_id": year_id, "name": "m", "ects": 5}

    assert client.post("/api/modules", json={**base, "grade": 6.5}).status_code == 422
    assert client.post("/api/modules", json={**base, "grade": 0.9}).status_code == 422
    assert client.post("/api/modules", json={**base, "ects": 7.5}).status_code == 422
    assert client.post("/api/modules", json={**base, "ects": 0}).status_code == 422
    assert client.post("/api/modules", json={**base, "name": ""}).status_code == 422
    assert client.post("/api/modules", json={**base, "year_id": 99}).status_code == 404
    assert client.get("/api/modules", params={"year_id": 99}).status_code == 404


def test_submodule_endpoints(client):
    year_id = client.post("/api/years", json={"year": "a"}).json()["id"]
    module_id = client.post("/api/modules", json={"year_id": year_id, "name": "m", "ects": 5}).json()["id"]

    created = client.post(
        "/api/submodules", json={"module_id": module_id, "name": "Klausur", "max_points": 90, "weight": 0.7}
    )
    assert created.status_code == 201
    submodule = created.json()
    assert set(submodule) == {"id", "module_id", "name", "max_points", "reached_points", "weight", "grade"}

    assert client.get("/api/submodules", params={"module_id": module_id}).json() == [submodule]
    assert client.get("/api/submodules").json() == [submodule]
    assert client.get("/api/submodules", params={"module_id": 99}).status_code == 404

    patched = client.patch(f"/api/submodules/{submodule['id']}", json={"reached_points": 80})
    assert patched.json()["reached_points"] == 80

    assert client.delete(f"/api/submodules/{submodule['id']}").status_code == 204
    assert client.get(f"/api/submodules/{submodule['id']}").status_code == 404


def test_submodule_validation(client):
    year_id = client.post("/api/years", json={"year": "a"}).json()["id"]
    module_id = client.post("/api/modules", json={"year_id": year_id, "name": "m", "ects": 5}).json()["id"]
    base = {"module_id": module_id, "name": "s", "max_points": 60, "weight": 1}

    assert client.post("/api/submodules", json={**base, "reached_points": 61}).status_code == 422
    assert client.post("/api/submodules", json={**base, "weight": 0}).status_code == 422
    assert client.post("/api/submodules", json={**base, "module_id": 99}).status_code == 404

    submodule_id = client.post("/api/submodules", json=base).json()["id"]
    too_many = client.patch(f"/api/submodules/{submodule_id}", json={"reached_points": 65})
    assert too_many.status_code == 422
    assert too_many.json() == {"detail": "Value error, reached_points must not exceed max_points"}


def _module_with_year(client, **fields):
    year_id = client.post("/api/years", json={"year": "a"}).json()["id"]
    return client.post("/api/modules", json={"year_id": year_id, "name": "m", "ects": 5, **fields}).json()


def _add_submodule(client, module_id, **fields):
    return client.post("/api/submodules", json={"module_id": module_id, "name": "s", "weight": 1, **fields})


def test_grades_from_table(client):
    module_id = _module_with_year(client)["id"]

    exam = _add_submodule(client, module_id, max_points=100, reached_points=83.5, weight=3).json()
    oral = _add_submodule(client, module_id, max_points=60).json()
    assert (exam["grade"], oral["grade"]) == (1.9, None)
    module = client.get(f"/api/modules/{module_id}").json()
    assert (module["grade"], module["passed"], module["grade_from_submodules"]) == (None, False, True)

    client.patch(f"/api/submodules/{oral['id']}", json={"reached_points": 30})
    module = client.get(f"/api/modules/{module_id}").json()
    assert (module["grade"], module["passed"]) == (2.42, True)

    client.patch(f"/api/submodules/{oral['id']}", json={"reached_points": 21})
    listed = client.get("/api/modules").json()[0]
    assert (listed["grade"], listed["passed"]) == (2.65, True)

    client.patch(f"/api/submodules/{exam['id']}", json={"reached_points": 0})
    client.patch(f"/api/submodules/{oral['id']}", json={"reached_points": 0})
    module = client.get(f"/api/modules/{module_id}").json()
    assert (module["grade"], module["passed"]) == (5.0, False)


def test_manual_grade_decides_passed(client):
    module = _module_with_year(client, grade=4.0)
    assert (module["grade"], module["passed"], module["grade_from_submodules"]) == (4.0, True, False)

    failed = client.patch(f"/api/modules/{module['id']}", json={"grade": 4.3}).json()
    assert failed["passed"] is False


def test_passed_only_without_grade(client):
    graded = _module_with_year(client, grade=2.0)
    rejected = client.patch(f"/api/modules/{graded['id']}", json={"passed": True})
    assert rejected.status_code == 422
    assert rejected.json() == {"detail": "passed can only be set on modules without grade and submodules"}

    assert _module_with_year(client, grade=2.0, passed=True) == {
        "detail": "passed can only be set on modules without grade and submodules"
    }

    switched = client.patch(f"/api/modules/{graded['id']}", json={"grade": None, "passed": True}).json()
    assert (switched["grade"], switched["passed"]) == (None, True)

    assert client.patch(f"/api/modules/{graded['id']}", json={"grade": 1.0}).status_code == 422


def test_grade_cannot_be_set_on_module_with_submodules(client):
    module_id = _module_with_year(client)["id"]
    _add_submodule(client, module_id, max_points=100, reached_points=100)

    response = client.patch(f"/api/modules/{module_id}", json={"grade": 3.0})
    assert response.status_code == 422
    assert response.json() == {"detail": "grade is calculated from the submodules and cannot be set"}
    assert client.patch(f"/api/modules/{module_id}", json={"passed": True}).status_code == 422
    assert client.patch(f"/api/modules/{module_id}", json={"name": "neu"}).json()["grade"] == 1.0


def test_submodule_rejected_on_graded_or_passed_module(client):
    graded = _module_with_year(client, grade=2.0)
    response = _add_submodule(client, graded["id"], max_points=100)
    assert response.status_code == 422
    assert response.json() == {"detail": "module has an entered grade, remove it before adding submodules"}

    passed = _module_with_year(client, passed=True)
    assert _add_submodule(client, passed["id"], max_points=100).status_code == 422
    assert client.get("/api/submodules", params={"module_id": passed["id"]}).json() == []


def test_submodule_max_points_must_have_table(client):
    module_id = _module_with_year(client)["id"]

    response = _add_submodule(client, module_id, max_points=20)
    assert response.status_code == 422
    assert response.json() == {"detail": "max_points must be one of [60, 90, 100, 120, 150, 180], got 20"}

    submodule_id = _add_submodule(client, module_id, max_points=100).json()["id"]
    assert client.patch(f"/api/submodules/{submodule_id}", json={"max_points": 75}).status_code == 422
    assert client.patch(f"/api/submodules/{submodule_id}", json={"max_points": 60}).json()["max_points"] == 60


def test_deleting_last_submodule_returns_to_manual_grading(client):
    module_id = _module_with_year(client)["id"]
    submodule_id = _add_submodule(client, module_id, max_points=100, reached_points=100).json()["id"]

    client.delete(f"/api/submodules/{submodule_id}")

    module = client.get(f"/api/modules/{module_id}").json()
    assert (module["grade"], module["grade_from_submodules"]) == (None, False)
    assert client.patch(f"/api/modules/{module_id}", json={"grade": 2.0}).status_code == 200


def test_supported_max_points(client):
    assert client.get("/api/grading/max-points").json() == [60, 90, 100, 120, 150, 180]
