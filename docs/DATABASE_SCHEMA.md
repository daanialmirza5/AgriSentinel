# AgriSentinel — Database Schema & Data Models

AgriSentinel utilizes **SQLite** for zero-configuration, reliable local persistence, managed via **SQLAlchemy ORM**.

---

## 1. Entity-Relationship Diagram (ERD)

```mermaid
erDiagram
    FIELD ||--o{ INSPECTION : contains
    FIELD ||--o{ TARGET : contains
    FIELD ||--o{ ROVER_SESSION : hosts
    INSPECTION ||--o{ DETECTION : extracts
    INSPECTION ||--o{ TARGET : generates
    TARGET ||--o{ INTERVENTION : receives
    ROVER_SESSION ||--o{ ROVER_EVENT : logs

    FIELD {
        string id PK
        string name
        string crop_type
        float width_m
        float length_m
        float row_spacing_m
        json restricted_zones
        datetime created_at
    }

    INSPECTION {
        string id PK
        string field_id FK
        string filename
        string media_type
        string model_backend_used
        int detection_count
        int target_count
        float processing_duration_ms
        string status
        datetime created_at
    }

    DETECTION {
        string id PK
        string inspection_id FK
        string class_name
        float confidence
        json bbox
        json center
        json field_coords
        datetime created_at
    }

    TARGET {
        string id PK
        string field_id FK
        string inspection_id FK
        string class_name
        float confidence
        float field_x
        float field_y
        float priority_score
        string status
        datetime created_at
        datetime completed_at
    }

    INTERVENTION {
        string id PK
        string target_id FK
        string field_id FK
        float duration_seconds
        string status
        json safety_snapshot
        datetime executed_at
    }

    ROVER_SESSION {
        string id PK
        string field_id FK
        string state
        float position_x
        float position_y
        float heading_rad
        float speed_mps
        string current_target_id FK
        datetime created_at
        datetime updated_at
    }

    ROVER_EVENT {
        string id PK
        string session_id FK
        string event_type
        json payload
        datetime created_at
    }
```

---

## 2. Table Specifications

### 2.1 `fields`
Stores parcel boundaries, physical dimensions in meters, and crop metadata.
- `id` (`VARCHAR(36)`, Primary Key)
- `name` (`VARCHAR(128)`, Not Null)
- `crop_type` (`VARCHAR(64)`)
- `width_m` (`FLOAT`, default `50.0`)
- `length_m` (`FLOAT`, default `30.0`)
- `row_spacing_m` (`FLOAT`, default `0.75`)
- `restricted_zones` (`JSON`, polygon coordinate arrays)
- `created_at` (`DATETIME`)

### 2.2 `inspections`
Records each image/video uploaded, inference timing, and model checkpoint used.
- `id` (`VARCHAR(36)`, Primary Key)
- `field_id` (`VARCHAR(36)`, Foreign Key $\rightarrow$ `fields.id`)
- `filename` (`VARCHAR(256)`)
- `media_type` (`VARCHAR(32)`, `image` or `video`)
- `model_backend_used` (`VARCHAR(64)`)
- `detection_count` (`INTEGER`, default `0`)
- `processing_duration_ms` (`FLOAT`)
- `status` (`VARCHAR(32)`, `COMPLETED`, `FAILED`)

### 2.3 `targets`
Actionable weed and crop targets projected into field metric space.
- `id` (`VARCHAR(36)`, Primary Key)
- `field_id` (`VARCHAR(36)`, Foreign Key $\rightarrow$ `fields.id`)
- `inspection_id` (`VARCHAR(36)`, Foreign Key $\rightarrow$ `inspections.id`)
- `class_name` (`VARCHAR(64)`)
- `confidence` (`FLOAT`)
- `field_x` (`FLOAT`)
- `field_y` (`FLOAT`)
- `priority_score` (`FLOAT`, normalized $0-1$)
- `status` (`VARCHAR(32)`, Enum: `NEW`, `APPROVED`, `REJECTED`, `IN_PROGRESS`, `COMPLETED`, `SKIPPED`)
- `created_at` (`DATETIME`)
- `completed_at` (`DATETIME`, Nullable)

### 2.4 `interventions`
Audit trail of all simulated spot treatments and safety verification snapshots.
- `id` (`VARCHAR(36)`, Primary Key)
- `target_id` (`VARCHAR(36)`, Foreign Key $\rightarrow$ `targets.id`)
- `field_id` (`VARCHAR(36)`, Foreign Key $\rightarrow$ `fields.id`)
- `duration_seconds` (`FLOAT`)
- `status` (`VARCHAR(32)`, `COMPLETED`, `ABORTED`)
- `safety_snapshot` (`JSON`, telemetry & sensor state at time of actuation)
- `executed_at` (`DATETIME`)
