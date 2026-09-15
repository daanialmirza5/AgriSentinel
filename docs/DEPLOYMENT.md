# Deployment

This build targets **local development only**. Nothing here is deployed
externally, and no cloud resources were created.

## Local development (the supported path)

### Backend

```powershell
# one-time setup
uv venv --python 3.12 .venv
uv pip install -p .venv\Scripts\python.exe -r backend\requirements.txt

# run
cd backend
$env:PYTHONPATH="."
..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

API docs: http://127.0.0.1:8000/docs
Health check: http://127.0.0.1:8000/api/health

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

Vite prints the actual port (default 5173, falls back to the next free
port if that's taken). The dev server proxies `/api` and `/media` to
`http://127.0.0.1:8000` (see `frontend/vite.config.ts`) so no CORS
configuration is needed in development beyond what's already set in
`backend/app/main.py`.

## Model installation

By default, on first run the backend attempts to download a small
pretrained COCO YOLOv8n model (~6MB) to `models/yolov8n.pt` purely to
demonstrate the real inference pipeline; it is always labeled as a generic,
non-agricultural detector. To install a real weed/crop model, see
`models/README.md` and `docs/DATASET_GUIDE.md`. To disable the network
download entirely (air-gapped environments), set
`AGRISENTINEL_ALLOW_GENERIC_MODEL=false` — the app will fall back to the
classical OpenCV vegetation-heuristic detector.

## CPU vs GPU inference

This build runs CPU-only inference (Ultralytics auto-selects CUDA if
`torch` detects a compatible GPU and CUDA build is installed, but
`backend/requirements.txt` pins the standard CPU-capable `ultralytics`
package without a CUDA-specific torch wheel). Expect single-image inference
in the 100-300ms range on a modern laptop CPU with the generic demo model;
a real agricultural model's speed depends on its architecture/size. Video
processing samples a bounded number of frames
(`MAX_VIDEO_SAMPLE_FRAMES` = 24 in `backend/app/config.py`) specifically to
keep CPU processing time bounded.

## Data storage & reset

All persistent data lives under `data/` (SQLite DB + uploaded/annotated
images) — see `data/README.md`. To fully reset: stop the backend and
delete `data/agrisentinel.db` (and optionally `data/uploads`,
`data/results`); it is recreated automatically on next startup.

## Configuration

All configuration is environment-variable based — see `.env.example` and
`backend/app/config.py`. There are no secrets to manage in this build (no
external API keys, no auth tokens).

## Optional Docker packaging (not built)

No `Dockerfile`/`docker-compose.yml` was created in this sprint. A future
containerized deployment would need: a Python 3.12-slim image with OpenCV's
system dependencies (`libgl1`, `libglib2.0-0`) for the backend, a
Node-based multi-stage build for the frontend static bundle served via
nginx or the FastAPI app itself, and a mounted volume for `data/` and
`models/` so uploads/DB/model weights persist across container restarts.
This was deliberately left undone rather than shipped untested.

## Troubleshooting

- **"ultralytics not importable" / model stuck in classical mode** — check
  `backend/requirements.txt` installed cleanly into `.venv`; classical
  vegetation-heuristic detection still works without it.
- **Camera won't start** — confirm no other application is holding the
  webcam, and that the reported device index actually exists
  (`GET /api/camera/devices`).
- **Port already in use** — Vite auto-increments; uvicorn will error if
  8000 is taken — pass `--port` to use another and update
  `frontend/vite.config.ts`'s proxy target accordingly.
- **CORS errors in the browser console** — only occurs if you bypass the
  Vite proxy and call the backend directly from a different origin; add
  that origin to `CORS_ORIGINS` in `backend/app/config.py`.
