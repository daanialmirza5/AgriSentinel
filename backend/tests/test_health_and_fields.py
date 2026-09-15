def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_model_status_reports_unavailable_without_model(client):
    r = client.get("/api/model/status")
    assert r.status_code == 200
    body = r.json()
    assert body["backend"] in ("classical", "yolo")
    assert "label" in body


def test_field_crud(client):
    r = client.post("/api/fields", json={"name": "F1", "width_m": 5, "length_m": 5})
    assert r.status_code == 201
    fid = r.json()["id"]

    r = client.get(f"/api/fields/{fid}")
    assert r.status_code == 200
    assert r.json()["name"] == "F1"

    r = client.patch(f"/api/fields/{fid}", json={"crop_type": "soy"})
    assert r.status_code == 200
    assert r.json()["crop_type"] == "soy"

    r = client.delete(f"/api/fields/{fid}")
    assert r.status_code == 204

    r = client.get(f"/api/fields/{fid}")
    assert r.status_code == 404


def test_field_requires_positive_dimensions(client):
    r = client.post("/api/fields", json={"name": "Bad", "width_m": -1, "length_m": 5})
    assert r.status_code == 422
