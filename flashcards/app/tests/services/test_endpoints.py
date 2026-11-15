EXAM = {"name": "Mathe", "exam_date": "2026-12-01T09:00:00+00:00"}


def test_exam_endpoints(client):
    created = client.post("/api/exams", json=EXAM)
    assert created.status_code == 201
    exam_id = created.json()["id"]

    assert client.get("/api/exams").json() == [created.json()]
    patched = client.patch(f"/api/exams/{exam_id}", json={"description": "Analysis"})
    assert patched.status_code == 200
    assert patched.json()["description"] == "Analysis"

    assert client.delete(f"/api/exams/{exam_id}").status_code == 204
    missing = client.get(f"/api/exams/{exam_id}")
    assert missing.status_code == 404
    assert missing.json() == {"detail": f"Exam with id {exam_id} not found"}


def test_deck_and_card_endpoints(client):
    exam_id = client.post("/api/exams", json=EXAM).json()["id"]
    deck = client.post("/api/decks", json={"exam_id": exam_id, "name": "Deck"}).json()
    assert client.get("/api/decks", params={"exam_id": exam_id}).json() == [deck]
    assert client.get("/api/decks").json() == []

    first = client.post("/api/cards", json={"deck_id": deck["id"], "front": "A", "back": "a"}).json()
    second = client.post("/api/cards", json={"deck_id": deck["id"], "front": "B", "back": "b"}).json()
    assert set(first) == {
        "id", "deck_id", "front", "front_image", "back", "back_image", "position", "state", "due", "last_review",
    }

    moved = client.put(f"/api/cards/{second['id']}/position", json={"position": 0})
    assert moved.json()["position"] == 0
    by_deck = client.get("/api/cards", params={"deck_id": deck["id"]}).json()
    assert [card["id"] for card in by_deck] == [second["id"], first["id"]]
    by_exam = client.get("/api/cards", params={"exam_id": exam_id, "due": True}).json()
    assert {card["id"] for card in by_exam} == {first["id"], second["id"]}

    assert client.patch(f"/api/cards/{first['id']}", json={"back": "neu"}).json()["back"] == "neu"
    assert client.delete(f"/api/cards/{first['id']}").status_code == 204
    assert client.get(f"/api/cards/{first['id']}").status_code == 404


def test_create_deck_unknown_exam(client):
    response = client.post("/api/decks", json={"exam_id": 5, "name": "Deck"})
    assert response.status_code == 404


def test_image_endpoints(client):
    uploaded = client.post("/api/uploads/images", files={"file": ("foto.png", b"png", "image/png")})
    assert uploaded.status_code == 201
    name = uploaded.json()

    fetched = client.get(f"/api/uploads/images/{name}")
    assert fetched.status_code == 200
    assert fetched.content == b"png"

    assert client.get("/api/uploads/images/missing.png").status_code == 404
    empty = client.post("/api/uploads/images", files={"file": ("foto.png", b"", "image/png")})
    assert empty.status_code == 415
