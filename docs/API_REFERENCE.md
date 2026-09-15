# AgriSentinel — REST API Reference

The AgriSentinel backend provides a RESTful API built on **FastAPI** with automatic OpenAPI documentation accessible at `http://127.0.0.1:8000/docs`.

---

## 1. System Health & Diagnostics

### `GET /api/health`
Returns backend health status, database connection viability, and timestamp.

**Response `200 OK`**:
```json
{
  "status": "ok",
  "database_ok": true,
  "timestamp": "2026-09-15T13:28:09.123456Z"
}
```

---

## 2. Fields Management

### `GET /api/fields`
List all configured field parcels.

### `POST /api/fields`
Create a new field parcel.

**Request Body**:
```json
{
  "name": "North Parcel Alpha",
  "crop_type": "Soybean",
  "width_m": 50.0,
  "length_m": 30.0,
  "row_spacing_m": 0.75,
  "restricted_zones": []
}
```

### `GET /api/fields/{id}`
Retrieve field details, crop rows, and target aggregates.

---

## 3. Computer Vision & Inspections

### `POST /api/inspections`
Upload an agricultural image or video for preprocessing, inference, and target extraction.

**Form Data Parameters**:
- `field_id` (*string*, required): Target field ID.
- `file` (*binary*, required): Image (`.jpg`, `.png`) or video file (`.mp4`).
- `backend_preference` (*string*, optional): `auto` | `yolo` | `classical_heuristic`.
- `conf_threshold` (*float*, optional): Detection confidence floor (default: `0.35`).

**Response `201 Created`**:
```json
{
  "id": "insp_9aa32904",
  "field_id": "field_01",
  "filename": "synthetic_demo_field.jpg",
  "annotated_image_path": "/media/results/annotated_demo.jpg",
  "model_backend_used": "classical_heuristic",
  "detection_count": 4,
  "target_count": 4,
  "processing_duration_ms": 45.2,
  "detections": [
    {
      "id": "det_01",
      "class_name": "weed",
      "confidence": 0.88,
      "bbox": { "x": 140, "y": 85, "width": 60, "height": 75 },
      "center": { "x": 170, "y": 122 },
      "field_coords": { "x": 12.4, "y": 8.3 }
    }
  ]
}
```

### `GET /api/inspections`
List inspection sessions with search, pagination, and filter parameters.

### `GET /api/inspections/{id}`
Fetch full inspection details, detections list, and annotated image URLs.

---

## 4. Target Management

### `GET /api/targets`
List targets with query filtering: `?field_id={id}&status={NEW|APPROVED|COMPLETED|REJECTED}`.

### `POST /api/targets/{id}/approve`
Approve a target for rover navigation and simulated treatment.

### `POST /api/targets/{id}/reject`
Reject or archive a false-positive target.

### `POST /api/targets/{id}/complete`
Mark a target manually as completed.

---

## 5. Rover Simulation & Control

### `GET /api/rover/status?field_id={field_id}`
Retrieve real-time rover telemetry, coordinates $(x, y)$, heading $\theta$, speed $v$, active target, and state machine status.

**Response `200 OK`**:
```json
{
  "session_id": "rov_session_01",
  "field_id": "field_01",
  "state": "NAVIGATING",
  "position": { "x": 14.2, "y": 9.1 },
  "heading_rad": 1.25,
  "speed_mps": 0.8,
  "target_id": "tgt_01",
  "distance_to_target_m": 3.45,
  "safety_status": "NORMAL"
}
```

### `POST /api/rover/start`
Initialize and ready the rover at starting position (`READY`).

### `POST /api/rover/navigate`
Command rover to navigate to target waypoint.
```json
{
  "field_id": "field_01",
  "target_id": "tgt_01"
}
```

### `POST /api/rover/pause`
Pause active navigation.

### `POST /api/rover/resume`
Resume paused navigation.

### `POST /api/rover/stop`
Cancel active mission and bring rover to a stop.

### `POST /api/rover/emergency-stop`
Immediate E-Stop trigger: cuts velocity to $0$ and locks state machine into `SAFETY_LOCK`.

### `POST /api/rover/reset`
Clear safety lock after operator audit.

---

## 6. Simulated Actuator

### `POST /api/actuator/simulate`
Trigger virtual spot treatment on target waypoint.

**Request Body**:
```json
{
  "target_id": "tgt_01",
  "operator_confirmed": true,
  "duration_seconds": 1.5
}
```

**Response `200 OK`**:
```json
{
  "status": "COMPLETED",
  "target_id": "tgt_01",
  "duration_s": 1.5,
  "message": "Simulated intervention completed successfully. No physical spray connected."
}
```

---

## 7. Analytics & Reports

### `GET /api/analytics?field_id={field_id}`
Returns aggregate metrics: detections over time, target status distribution, class breakdown, and intervention efficiency.

### `GET /api/reports/inspections/csv`
Download inspection history as a formatted CSV file.

### `GET /api/reports/targets/csv`
Download target inventory as a formatted CSV file.

---

## 8. Settings & Model Status

### `GET /api/settings`
Retrieve current system settings, detection backend preference, confidence threshold, and camera configs.

### `PUT /api/settings`
Update configuration values.

### `GET /api/model/status`
Check currently loaded model checkpoint, device (CPU/CUDA), and generic fallback status.

### `POST /api/model/reload`
Hot-reload model weights from `models/` directory.
