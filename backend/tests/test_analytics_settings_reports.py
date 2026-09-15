def test_analytics_summary_empty_state(client, field):
    r = client.get(f"/api/analytics/summary?field_id={field['id']}")
    assert r.status_code == 200
    body = r.json()
    assert body["total_inspections"] == 0
    assert body["total_detections"] == 0
    assert body["average_confidence"] is None


def test_analytics_summary_after_inspection(client, field, sample_image_bytes):
    client.patch("/api/settings", json={"values": {"detection_backend_preference": "classical"}})
    files = {"file": ("sample.jpg", sample_image_bytes, "image/jpeg")}
    client.post(f"/api/inspect/image?field_id={field['id']}", files=files)

    r = client.get(f"/api/analytics/summary?field_id={field['id']}")
    body = r.json()
    assert body["total_inspections"] == 1
    assert body["total_detections"] >= 1
    assert body["average_confidence"] is not None


def test_settings_roundtrip(client):
    r = client.patch("/api/settings", json={"values": {"confidence_threshold": 0.5}})
    assert r.status_code == 200
    assert r.json()["values"]["confidence_threshold"] == 0.5

    r = client.get("/api/settings")
    assert r.json()["values"]["confidence_threshold"] == 0.5


def test_reports_csv_export(client, field, sample_image_bytes):
    client.patch("/api/settings", json={"values": {"detection_backend_preference": "classical"}})
    files = {"file": ("sample.jpg", sample_image_bytes, "image/jpeg")}
    client.post(f"/api/inspect/image?field_id={field['id']}", files=files)

    r = client.get("/api/reports/inspections.csv")
    assert r.status_code == 200
    assert "id,field_id" in r.text

    r = client.get("/api/reports/targets.csv")
    assert r.status_code == 200
    assert "priority_score" in r.text
