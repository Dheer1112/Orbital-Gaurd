"""
ORBITAL GUARD — Frontend Integration Server
Wraps backend.service.run_scenario for the PS-02 Orbital Command Center UI.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is on path
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import Optional

from backend.service import run_scenario, list_demo_scenarios

app = FastAPI(
    title="ORBITAL GUARD API",
    description="Decision-support API for space-debris collision avoidance (simulation only)",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIR = ROOT / "frontend"


class RunRequest(BaseModel):
    scenario: str = Field(default="HIGH_RISK", description="Demo scenario key")
    confidence_threshold: float = Field(default=0.35, ge=0.0, le=1.0)
    min_acceptable_miss_km: float = Field(default=0.5, ge=0.0)


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "ORBITAL GUARD", "mode": "OFFLINE_DEMO"}


@app.get("/api/scenarios")
def scenarios():
    return {"scenarios": list_demo_scenarios()}


@app.post("/api/run")
def run(req: RunRequest):
    try:
        result = run_scenario(
            scenario_key=req.scenario,
            confidence_threshold=req.confidence_threshold,
            min_acceptable_miss_km=req.min_acceptable_miss_km,
        )
        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=result)
        return JSONResponse(content=result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "error": str(e),
                "hint": "Check that models/edge/gbdt.joblib exists and dependencies are installed.",
            },
        )


@app.get("/")
def index():
    index_path = FRONTEND_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="Frontend not found")
    return FileResponse(index_path)


# Optional: serve any extra static assets later
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
