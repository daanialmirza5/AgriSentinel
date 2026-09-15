def _create_target(client, field, sample_image_bytes):
    client.patch("/api/settings", json={"values": {"detection_backend_preference": "classical"}})
    files = {"file": ("sample.jpg", sample_image_bytes, "image/jpeg")}
    r = client.post(f"/api/inspect/image?field_id={field['id']}", files=files)
    targets = client.get(f"/api/targets?field_id={field['id']}").json()
    assert len(targets) >= 1
    return targets[0]


def test_target_lifecycle(client, field, sample_image_bytes):
    target = _create_target(client, field, sample_image_bytes)
    tid = target["id"]

    r = client.post(f"/api/targets/{tid}/approve")
    assert r.status_code == 200
    assert r.json()["status"] == "SELECTED"
    assert r.json()["operator_approved"] is True

    r = client.post(f"/api/targets/{tid}/plan")
    assert r.status_code == 200
    assert r.json()["status"] == "PLANNED"

    r = client.post(f"/api/targets/{tid}/skip")
    assert r.status_code == 200
    assert r.json()["status"] == "SKIPPED"


def test_target_filter_by_status(client, field, sample_image_bytes):
    target = _create_target(client, field, sample_image_bytes)
    client.post(f"/api/targets/{target['id']}/approve")

    r = client.get(f"/api/targets?field_id={field['id']}&status=SELECTED")
    assert r.status_code == 200
    assert all(t["status"] == "SELECTED" for t in r.json())


def test_plan_rejects_invalid_transition(client, field, sample_image_bytes):
    target = _create_target(client, field, sample_image_bytes)
    client.post(f"/api/targets/{target['id']}/skip")
    r = client.post(f"/api/targets/{target['id']}/plan")
    assert r.status_code == 400
