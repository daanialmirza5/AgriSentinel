# AgriSentinel — Hackathon & Live Demo Script

Use this step-by-step demonstration script to present **AgriSentinel** to judges, agronomists, and technical audiences in under 5 minutes.

---

## 1. Demo Narrative & Pitch

> "Traditional farming uses blanket chemical spraying—costly, inefficient, and harmful to ecosystems. **AgriSentinel** provides a precision agriculture platform combining computer vision for weed detection, planar homography for target localization, and a simulation-first robotics engine with multi-tier safety interlocking."

---

## 2. Step-by-Step Live Walkthrough

| Step | Page & Action | What to Explain to Audience | Expected Visual Outcome |
| :--- | :--- | :--- | :--- |
| **1. System Overview** | Navigate to `http://localhost:5173/` | Point out real aggregate statistics (fields, inspections, targets) and active detection backend status. | Main dashboard with zero fake stats. |
| **2. Field Setup** | Go to **Settings** $\rightarrow$ Click **Create Demo Field** | Configure field parcel dimensions ($50\text{m} \times 30\text{m}$), crop rows, and safety settings. | `North Parcel Alpha` created and selected in top bar. |
| **3. Computer Vision** | Go to **Vision Lab** $\rightarrow$ Click **Load synthetic demo sample** $\rightarrow$ Click **Run Inference** | Explain the OpenCV preprocessing (CLAHE contrast normalization) and the classical/YOLO detection head. | Annotated bounding boxes appear over weed clusters with confidence scores and processing duration ($<50\text{ms}$). |
| **4. Target Approval** | Go to **Targets** | Review newly generated targets. Explain the transparent priority score combining confidence, severity, and proximity. | Click **Approve** on target `#1`. Status changes to `APPROVED`. |
| **5. Field Map** | Go to **Field Map** | Point out the 2D SVG canvas rendering field boundaries, crop rows, rover initial position, and target waypoints. | Approved target rendered as active icon on map. |
| **6. Autonomous Rover** | Go to **Rover Simulation** $\rightarrow$ Click **Start Rover** $\rightarrow$ Select Target $\rightarrow$ Click **Navigate to Target** | Explain 2D differential-drive kinematics and real-time waypoint tracking. | Rover visibly navigates along trajectory; distance decrements until status becomes `ARRIVED` $\rightarrow$ `INTERVENTION_PENDING`. |
| **7. Safety Interlock** | Click **Run Simulated Intervention at Target** | Explain the 5-tier safety check (Rover stationary, confidence $\ge 0.35$, within bounds, operator confirmed). | Simulated actuator activates for $1.5\text{s}$; target updates to `COMPLETED`. |
| **8. Emergency Stop** | Click **Emergency Stop** $\rightarrow$ Click **Reset Safety Lock** | Demonstrate instant fail-safe response locking rover controls. | System enters `SAFETY_LOCK` banner; reset restores system to `IDLE`. |
| **9. Audit & Analytics** | Go to **Inspection History** & **Analytics** | Review persistent SQLite logs, detection distributions over time, and CSV export functionality. | Dynamic charts and tables reflect real recorded actions. |
| **10. OpenAPI Docs** | Open `http://localhost:8000/docs` | Show the FastAPI OpenAPI / Swagger interactive documentation. | Interactive Swagger UI with all 20+ tested endpoints. |

---

## 3. Anticipated Q&A

**Q: Is physical chemical spraying implemented?**  
*A: No. AgriSentinel is strictly simulation-first for software safety. The actuator is simulated and safety-interlocked; hardware integration guidelines are documented in `docs/HARDWARE_INTEGRATION.md`.*

**Q: What happens if no custom weed model is provided?**  
*A: The system provides a transparent classical vegetation segmentation fallback using normalized Excess Green ($2G - R - B$) indices and Otsu binarization, clearly labeled in the UI.*
