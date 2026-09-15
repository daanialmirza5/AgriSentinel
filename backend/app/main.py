from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import actuator, analytics, camera, fields, health, inspections, reports, rover, settings, targets
from app.config import CORS_ORIGINS, DATA_DIR
from app.database import init_db

app = FastAPI(
    title="AgriSentinel API",
    description=(
        "AI precision-agriculture rover platform. Simulation-first: rover "
        "navigation and actuation are virtual. See /api/model/status for "
        "whether real trained-model inference is active."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


app.mount("/media", StaticFiles(directory=str(DATA_DIR)), name="media")

api_prefix = "/api"
app.include_router(health.router, prefix=api_prefix)
app.include_router(fields.router, prefix=api_prefix)
app.include_router(inspections.router, prefix=api_prefix)
app.include_router(camera.router, prefix=api_prefix)
app.include_router(targets.router, prefix=api_prefix)
app.include_router(rover.router, prefix=api_prefix)
app.include_router(actuator.router, prefix=api_prefix)
app.include_router(analytics.router, prefix=api_prefix)
app.include_router(settings.router, prefix=api_prefix)
app.include_router(reports.router, prefix=api_prefix)


@app.get("/")
def root():
    return {"name": "AgriSentinel API", "docs": "/docs", "health": "/api/health"}
