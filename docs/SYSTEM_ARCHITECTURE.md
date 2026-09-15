# AgriSentinel — System Architecture

This document provides a comprehensive technical overview of the **AgriSentinel** platform architecture, detailing component interactions, data flow, safety interlocks, computer vision pipelines, and database models.

---

## 1. High-Level Architecture Diagram

```mermaid
flowchart TB
    subgraph Client ["Frontend Layer (React 18 + TypeScript + Vite)"]
        UI_Overview["Overview Dashboard"]
        UI_Vision["Vision Lab (Upload & Inference)"]
        UI_Live["Live Monitoring (Camera Feed)"]
        UI_Rover["Rover Simulation & Telemetry"]
        UI_Map["2D SVG Field Map"]
        UI_Targets["Target Management"]
        UI_History["Inspection History"]
        UI_Analytics["Analytics & Reporting"]
        UI_Settings["Settings & Field CRUD"]
    end

    subgraph Gateway ["API & Service Layer (FastAPI)"]
        Router_Health["/api/health"]
        Router_Fields["/api/fields"]
        Router_Inspections["/api/inspections"]
        Router_Vision["/api/camera & /api/model"]
        Router_Targets["/api/targets"]
        Router_Rover["/api/rover"]
        Router_Actuator["/api/actuator"]
        Router_Analytics["/api/analytics"]
        Router_Settings["/api/settings"]
    end

    subgraph CV_Engine ["Computer Vision & Localization Engine"]
        CV_Preprocess["OpenCV Preprocessing (CLAHE, Blur, HSV)"]
        CV_YOLO["YOLOv8 Inference Engine (Ultralytics)"]
        CV_Fallback["Classical Vegetation Segmentation"]
        CV_Localizer["Planar Homography Ground-Plane Localizer"]
        CV_Annotator["Bounding Box & Mask Annotator"]
    end

    subgraph Robotics_Engine ["Robotics & Simulation Engine"]
        Sim_Rover["2D Kinematic Rover Simulator"]
        Sim_Planner["Trajectory & Waypoint Planner"]
        Sim_Actuator["Simulated Actuator Controller"]
        Safety_Core["Multi-Layer Safety & E-Stop Interlock"]
    end

    subgraph Storage ["Persistence & Storage Layer"]
        DB[(SQLite Database)]
        FS_Uploads["data/uploads/ (Raw Imagery)"]
        FS_Results["data/results/ (Annotated Imagery)"]
        FS_Models["models/ (Weight Checkpoints)"]
    end

    %% Interactions
    Client <-->|REST API JSON & Static Media| Gateway
    Gateway --> CV_Engine
    Gateway --> Robotics_Engine
    CV_Engine --> Storage
    Robotics_Engine --> Storage
    Gateway <-->|SQLAlchemy ORM| DB
```

---

## 2. Component Breakdown

### 2.1 Frontend Client (`frontend/src/`)
Built with **React 18**, **TypeScript**, and **Vite**, using a hand-crafted CSS design system inspired by high-density mission-control interfaces.
- **State Management**: React Context API (`FieldContext`, `FieldProvider`) managing active field selection, telemetry synchronization, and target states.
- **Visual Map Engine**: 2D SVG canvas rendering field boundaries, crop rows, restricted zones, real-time rover heading, and target markers.
- **Responsive Telemetry Stream**: Polling intervals synchronize rover position, velocity, heading, and state machine transitions.

### 2.2 Backend API Gateway (`backend/app/`)
Developed with **FastAPI** and **Pydantic** for high-throughput asynchronous execution and strict validation.
- **Modular Routers**: Isolated endpoint routers for fields, inspections, targets, rover telemetry, actuator triggers, and analytics.
- **Static File Server**: Mounted `/media` static router serving raw uploads and annotated results securely.
- **Dependency Injection**: SQLAlchemy session management with transactional integrity and rollback handling.

### 2.3 Computer Vision Pipeline (`backend/app/services/`)
- **`preprocessing.py`**: Performs CLAHE (Contrast Limited Adaptive Histogram Equalization), bilateral filtering, color conversions, and image resizing.
- **`inference.py`**: Wraps Ultralytics `YOLO` model loader with safe error trapping. Evaluates class thresholds and provides transparent fallback to classical HSV green-excess indexing ($2G - R - B$).
- **`localization.py`**: Calculates perspective transformation matrices ($3 \times 3$ homography) mapping image pixels $(u, v)$ to field coordinates $(x, y)$ in meters.

### 2.4 Robotics Simulator & Safety Core
- **`rover_simulator.py`**: Simulates 2D differential-drive kinematics with Euler integration. Updates position, heading, velocity, and distance-to-waypoint at discrete time steps ($\Delta t$).
- **`safety.py`**: Evaluates operating parameters against safety thresholds (e.g. maximum navigation speed, target confidence $> \theta_{\text{min}}$, non-emergency status, boundary containment).
- **`actuator.py`**: Simulates precision spot application with safety interlocks, operator approval gating, and duration timers.

---

## 3. End-to-End Sequence Diagram

```mermaid
sequenceDiagram
    autonumber
    actor Operator
    participant UI as Web Dashboard (React)
    participant API as FastAPI Backend
    participant CV as Vision Pipeline
    participant DB as SQLite DB
    participant Sim as Rover Simulator

    Operator->>UI: Upload agricultural image & run inference
    UI->>API: POST /api/inspections (multipart/form-data)
    API->>CV: Preprocess image & run YOLOv8/HSV inference
    CV->>CV: Compute bounding boxes, confidence, & homography
    CV-->>API: Detections + Field Coordinates + Annotated JPG
    API->>DB: Persist Inspection, Detections, & New Targets
    API-->>UI: Inspection complete with localized targets

    Operator->>UI: Review and Approve Target #1
    UI->>API: POST /api/targets/1/approve
    API->>DB: Update Target status -> APPROVED

    Operator->>UI: Start Rover & Command Navigation to Target #1
    UI->>API: POST /api/rover/navigate {target_id: 1}
    API->>Sim: Compute trajectory & transition state -> NAVIGATING
    Sim-->>API: Rover moving...
    API-->>UI: Live telemetry stream (x, y, theta, distance)

    Note over Sim,UI: Rover reaches target tolerance (< 0.2m)
    Sim->>Sim: Transition state -> ARRIVED -> INTERVENTION_PENDING
    Sim-->>UI: State: INTERVENTION_PENDING

    Operator->>UI: Confirm and Trigger Simulated Intervention
    UI->>API: POST /api/actuator/simulate {target_id: 1}
    API->>API: Verify Safety Engine & Operator Approval Gates
    API->>DB: Record Intervention & update Target -> COMPLETED
    API-->>UI: Intervention successful (Logged to DB)
```

---

## 4. Security & Isolation Boundaries

1. **Local-First Sandboxing**: By default, AgriSentinel runs locally on `127.0.0.1`. No data or imagery leaves the host machine.
2. **File Validation**: Strict MIME-type checking, file size ceilings (max 50MB), and path sanitization prevent path traversal attacks.
3. **Emergency Disconnect**: The Emergency Stop endpoint (`POST /api/rover/emergency-stop`) immediately locks the simulator and disarms actuator triggers at the service layer.
