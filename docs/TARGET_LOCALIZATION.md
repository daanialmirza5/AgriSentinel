# AgriSentinel — Target Localization & Calibration Guide

This document specifies the coordinate transformation models and calibration methods used by **AgriSentinel** to map 2D image pixel detections into real-world 2D field coordinates.

---

## 1. Coordinate Frames Definition

AgriSentinel defines three primary coordinate reference frames:

```
[Pixel Frame (u, v)]  --->  [Camera Optical Frame (Xc, Yc, Zc)]  --->  [World / Field Frame (Xw, Yw)]
 (Origin: Top-Left)          (Origin: Camera Lens Center)               (Origin: Field Corner (0,0)m)
```

1. **Pixel Image Frame ($\mathcal{F}_i$)**: Origin at top-left corner of the image $(0, 0)\text{ px}$, $u$ extending rightward (columns), $v$ extending downward (rows).
2. **Rover Body Frame ($\mathcal{F}_b$)**: Origin at the rover's center of differential-drive axle. $X_b$ points forward along heading $\theta$, $Y_b$ points to the left.
3. **World Field Frame ($\mathcal{F}_w$)**: Global Cartesian frame in meters. $(0, 0)$ is the southwest corner of the field parcel, with $X_w$ spanning East and $Y_w$ spanning North.

---

## 2. Planar Homography Projection

Assuming the camera observes a flat ground plane ($Z_w = 0$), the transformation between homogeneous pixel coordinates $\tilde{\mathbf{p}} = [u, v, 1]^T$ and ground plane coordinates $\tilde{\mathbf{P}}_w = [X_w, Y_w, 1]^T$ is governed by the $3 \times 3$ Homography matrix $\mathbf{H}$:

$$\tilde{\mathbf{p}} = \mathbf{H} \tilde{\mathbf{P}}_w = \begin{bmatrix} h_{11} & h_{12} & h_{13} \\ h_{21} & h_{22} & h_{23} \\ h_{31} & h_{32} & h_{33} \end{bmatrix} \begin{bmatrix} X_w \\ Y_w \\ 1 \end{bmatrix}$$

Given 4 or more non-collinear ground-truth calibration points $(u_i, v_i) \leftrightarrow (X_i, Y_i)$, $\mathbf{H}$ is solved via Singular Value Decomposition (SVD) using OpenCV's `cv2.findHomography()`.

---

## 3. Calibration Procedure for Real Deployments

To calibrate a real downward-facing camera mounted on an agricultural rover:

```
+-------------------------------------------------------------+
| Step 1: Place 4 visible ArUco or high-contrast markers on    |
|         the ground in a known rectangle (e.g. 2.0m x 1.5m). |
| Step 2: Capture a calibration frame from the rover camera.  |
| Step 3: Extract pixel corners (u1,v1), (u2,v2), ...         |
| Step 4: Compute homography matrix H.                        |
| Step 5: Validate re-projection error (must be < 1.5 cm).    |
+-------------------------------------------------------------+
```

```python
import cv2
import numpy as np

# Pixel coordinates of 4 marker corners
pts_img = np.float32([[120, 100], [520, 105], [590, 440], [50, 435]])

# Corresponding real-world metric coordinates relative to rover center (meters)
pts_world = np.float32([[-0.75, 2.0], [0.75, 2.0], [0.75, 0.5], [-0.75, 0.5]])

# Compute homography matrix
H, status = cv2.findHomography(pts_img, pts_world)
```

---

## 4. Default Simulated Localization

In the simulation environment where no physical camera calibration file is provided:
- AgriSentinel assumes a virtual nadir camera footprint of $3.0\text{ m} \times 2.0\text{ m}$ centered at the rover's current spatial coordinates $(x_r, y_r)$ with heading angle $\theta_r$.
- Centroid pixel offsets are projected onto the ground plane using trigonometric rotation.

> [!WARNING]
> In simulated mode, field coordinates are estimated. Field coordinates require physical camera calibration and RTK-GPS integration before physical robotic sprayers can be guided safely.
