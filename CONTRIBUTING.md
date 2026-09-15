# Contributing to AgriSentinel

Thank you for your interest in contributing to **AgriSentinel** — an open-source, simulation-first precision agriculture and computer vision platform.

---

## 1. Code of Conduct & Simulation Transparency

AgriSentinel is built on principles of scientific honesty and safety transparency:
* **Honest Disclosures**: Never represent simulated features as physical hardware controllers unless verified on actual hardware testbenches.
* **No Fabricated Statistics**: Precision, recall, and detection accuracy must only be stated if measured on real ground-truth datasets.
* **Safety First**: Any modifications to the safety engine, emergency stop logic, or actuation gates must pass rigorous unit testing and require explicit operator confirmation defaults.

---

## 2. Development Setup

### Prerequisites
- **Python 3.12+**
- **Node.js 18+ & npm**
- **Git**

### Backend Setup
```powershell
# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\activate

# Install dependencies
pip install -r backend\requirements.txt

# Run backend server
$env:PYTHONPATH="backend"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### Frontend Setup
```powershell
cd frontend
npm install
npm run dev
```

---

## 3. Pull Request Guidelines

1. **Fork and Branch**: Create a feature branch with a descriptive name (`feat/model-export-tensorrt` or `fix/homography-aspect-ratio`).
2. **Coding Standards**:
   - Backend: Follow PEP 8, write type hints, use Pydantic models for request/response schemas.
   - Frontend: Follow React TypeScript best practices, use modular components, adhere to the established design system tokens in `index.css`.
3. **Automated Testing**:
   - Ensure all pytest tests pass before opening a PR:
     ```powershell
     python -m pytest backend/tests -v
     ```
   - Ensure frontend builds without type errors:
     ```powershell
     cd frontend; npm run build
     ```
4. **Documentation**: Update relevant documentation files in `docs/` if modifying APIs, safety gates, or computer vision pipelines.

---

## 4. Issue Reporting

When reporting bugs or feature requests:
- Specify operating system, Python version, Node.js version, and browser.
- Include reproduction steps and exact error logs.
- Disclose whether custom YOLO weights or default classical heuristics were used.

---

## 5. Ownership & License

By contributing to AgriSentinel, you agree that your contributions will be licensed under the project's [MIT License](LICENSE).
