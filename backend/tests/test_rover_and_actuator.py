import time


def _create_target(client, field, sample_image_bytes):
    client.patch("/api/settings", json={"values": {"detection_backend_preference": "classical"}})
    files = {"file": ("sample.jpg", sample_image_bytes, "image/jpeg")}
    client.post(f"/api/inspect/image?field_id={field['id']}", files=files)
    targets = client.get(f"/api/targets?field_id={field['id']}").json()
    return targets[0]


def test_rover_start_and_status(client, field):
    r = client.post("/api/rover/simulation/start", json={"field_id": field["id"]})
    assert r.status_code == 200
    assert r.json()["status"] == "READY"

    r = client.get(f"/api/rover/status?field_id={field['id']}")
    assert r.status_code == 200
    assert r.json()["status"] == "READY"


def test_rover_navigate_and_arrive(client, field, sample_image_bytes):
    target = _create_target(client, field, sample_image_bytes)
    client.post("/api/rover/simulation/start", json={"field_id": field["id"]})

    r = client.post("/api/rover/navigate", json={"target_id": target["id"]})
    assert r.status_code == 200
    assert r.json()["status"] == "NAVIGATING"

    # Field is 10x10m; rover moves ~1.2 m/s. Poll status until arrival or timeout.
    deadline = time.time() + 20
    status = None
    while time.time() < deadline:
        status = client.get(f"/api/rover/status?field_id={field['id']}").json()
        if status["status"] == "INTERVENTION_PENDING":
            break
        time.sleep(0.5)
    assert status is not None
    assert status["status"] == "INTERVENTION_PENDING"


def test_emergency_stop_blocks_navigation_and_requires_reset(client, field, sample_image_bytes):
    target = _create_target(client, field, sample_image_bytes)
    client.post("/api/rover/simulation/start", json={"field_id": field["id"]})
    r = client.post(f"/api/rover/emergency-stop?field_id={field['id']}")
    assert r.status_code == 200
    assert r.json()["safety_state"] == "ESTOP"
    assert r.json()["status"] == "SAFETY_LOCK"

    r = client.post("/api/rover/navigate", json={"target_id": target["id"]})
    assert r.status_code == 409

    r = client.post(f"/api/rover/reset?field_id={field['id']}")
    assert r.status_code == 200
    assert r.json()["safety_state"] == "NORMAL"


def test_actuator_blocks_low_confidence_target(client, field):
    from app.database import SessionLocal
    from app.models import Detection, Inspection, Target

    db = SessionLocal()
    insp = Inspection(field_id=field["id"], source_type="image", status="completed")
    db.add(insp)
    db.flush()
    det = Detection(
        inspection_id=insp.id, class_name="vegetation_region", target_type="unclassified_vegetation",
        confidence=0.1, field_x=1.0, field_y=1.0, localization_confidence="approximate",
    )
    db.add(det)
    db.flush()
    tgt = Target(detection_id=det.id, field_id=field["id"], status="DETECTED")
    db.add(tgt)
    db.commit()
    tgt_id = tgt.id
    db.close()

    r = client.post("/api/actuator/simulate", json={"target_id": tgt_id, "operator_approved": True})
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is False
    assert body["safety_checks"]["confidence_ok"] is False


def test_actuator_requires_operator_approval_by_default(client, field, sample_image_bytes):
    target = _create_target(client, field, sample_image_bytes)
    r = client.post("/api/actuator/simulate", json={"target_id": target["id"], "operator_approved": False})
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is False
    assert "operator_approved" in body["safety_checks"]
    assert body["safety_checks"]["operator_approved"] is False


def test_actuator_succeeds_with_approval_and_good_confidence(client, field):
    from app.database import SessionLocal
    from app.models import Detection, Inspection, Target

    db = SessionLocal()
    insp = Inspection(field_id=field["id"], source_type="image", status="completed")
    db.add(insp)
    db.flush()
    det = Detection(
        inspection_id=insp.id, class_name="weed", target_type="weed",
        confidence=0.9, field_x=1.0, field_y=1.0, localization_confidence="approximate",
    )
    db.add(det)
    db.flush()
    tgt = Target(detection_id=det.id, field_id=field["id"], status="DETECTED")
    db.add(tgt)
    db.commit()
    tgt_id = tgt.id
    db.close()

    r = client.post("/api/actuator/simulate", json={"target_id": tgt_id, "operator_approved": True})
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert body["status"] == "COMPLETED"
