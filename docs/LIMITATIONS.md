# AgriSentinel — System Boundaries & Limitations

In accordance with AgriSentinel's core philosophy of scientific transparency, this document explicitly lists current system limitations, simulation constraints, and hardware boundaries.

---

## 1. Computer Vision & Model Boundaries

- **No Proprietary Field Dataset Bundled**: The repository ships with training and validation scripts (`ml/train.py`), but does not bundle large proprietary agricultural weight checkpoints. Users can mount custom YOLO checkpoints (`models/weed_crop_model.pt`) or utilize the built-in classical vegetation heuristic ($2G - R - B$).
- **Illumination Sensitivity**: The classical heuristic relies on green-excess color segmentation and may be affected by extreme shadows, muddy water puddles, or non-green weeds without CLAHE pre-filtering.
- **2D Planar Assumption**: Object detection operates on 2D image coordinates without 3D depth point-cloud reconstruction.

---

## 2. Robotics & Simulation Boundaries

- **Software-in-the-Loop Simulation**: Rover movement, kinematics, and obstacle avoidance are simulated in software. No physical serial motor controllers or CAN bus interfaces are driven directly by default.
- **Flat Ground Model**: Kinematics assume a flat, 2D continuous Cartesian plane without uneven ruts, mud slippage, or slope roll/pitch dynamics.
- **Virtual Actuator**: The spot-spraying actuator is virtual and logs simulated duration events. No physical high-pressure chemical pumps or solenoids are connected.

---

## 3. Localization & Sensing Boundaries

- **Estimated Coordinates**: Pixel-to-field localization utilizes a planar homography approximation. Accurate centimeter-level outdoor localization requires physical intrinsic camera calibration and RTK-GNSS fusion.
- **Webcam Browser Constraints**: The live monitoring interface relies on standard browser media device permissions (`getUserMedia`) or backend OpenCV capture indices.

---

## 4. Operational & Agronomic Disclosures

- **No Agronomic Guarantees**: AgriSentinel does not make automated claims regarding exact percentage crop yield increases or commercial herbicide volume reductions without field validation.
- **Human-in-the-Loop Requirement**: The platform is configured by default to require human operator confirmation before any simulated intervention is authorized.
