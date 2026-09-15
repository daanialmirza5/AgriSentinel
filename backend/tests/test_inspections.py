def test_inspect_image_creates_inspection_and_targets(client, field, sample_image_bytes):
    r = client.patch("/api/settings", json={"values": {"detection_backend_preference": "classical"}})
    assert r.status_code == 200

    files = {"file": ("sample.jpg", sample_image_bytes, "image/jpeg")}
    r = client.post(f"/api/inspect/image?field_id={field['id']}", files=files)
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "completed"
    assert body["detection_mode"] == "classical_vegetation_heuristic"
    assert body["detection_count"] >= 1
    assert len(body["detections"]) == body["detection_count"]
    for d in body["detections"]:
        assert d["target_type"] == "unclassified_vegetation"
        assert d["localization_confidence"] == "approximate"

    r = client.get(f"/api/inspections?field_id={field['id']}")
    assert r.status_code == 200
    assert len(r.json()) == 1

    r = client.get(f"/api/targets?field_id={field['id']}")
    assert r.status_code == 200
    targets = r.json()
    assert len(targets) == body["detection_count"]
    assert all(t["status"] in ("DETECTED", "REVIEW_REQUIRED") for t in targets)


def test_inspect_image_rejects_bad_extension(client, field):
    files = {"file": ("sample.txt", b"not an image", "text/plain")}
    r = client.post(f"/api/inspect/image?field_id={field['id']}", files=files)
    assert r.status_code == 400


def test_inspect_image_rejects_missing_field(client, sample_image_bytes):
    files = {"file": ("sample.jpg", sample_image_bytes, "image/jpeg")}
    r = client.post("/api/inspect/image?field_id=does-not-exist", files=files)
    assert r.status_code == 404


def test_inspect_image_rejects_corrupt_file(client, field):
    files = {"file": ("sample.jpg", b"\x00\x01\x02not-a-real-jpeg", "image/jpeg")}
    r = client.post(f"/api/inspect/image?field_id={field['id']}", files=files)
    assert r.status_code == 400


def test_delete_inspection(client, field, sample_image_bytes):
    files = {"file": ("sample.jpg", sample_image_bytes, "image/jpeg")}
    r = client.post(f"/api/inspect/image?field_id={field['id']}", files=files)
    insp_id = r.json()["id"]
    r = client.delete(f"/api/inspections/{insp_id}")
    assert r.status_code == 204
    r = client.get(f"/api/inspections/{insp_id}")
    assert r.status_code == 404
