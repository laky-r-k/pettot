"""PetTot FastAPI backend and static owner frontend."""

import os
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from models.Visual_Grimace_Calculator import GrimacePainDetector
from models.Incision_Change_Detection import IncisionScanner

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR / "frontend"

app = FastAPI(
    title="PetTot Recovery API",
    description=(
        "Prototype endpoints for experimental pet facial-feature analysis and "
        "baseline/current incision image comparison. These outputs are not diagnoses."
    ),
    version="1.1.0",
)

# The frontend is normally served from this same local origin. This list only
# opens the optional local static-server origins used during UI development.
allowed_origins = [
    origin.strip()
    for origin in os.environ.get(
        "PETTOT_CORS_ORIGINS",
        "http://127.0.0.1:5500,http://localhost:5500,http://127.0.0.1:8000,http://localhost:8000",
    ).split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

grimace_detector = GrimacePainDetector(gemini_api_key=os.environ.get("GEMINI_API_KEY"))
incision_scanner = IncisionScanner()


@app.get("/health", tags=["Health"])
async def health_check():
    """Return a small health response for the local frontend connection test."""
    return {
        "status": "online",
        "service": "PetTot API (prototype)",
        "models": ["Visual_Grimace_Calculator", "Incision_Change_Detection"],
    }


@app.post("/api/grimace/analyze", tags=["Experimental face analysis"])
async def analyze_grimace(
    file: UploadFile = File(..., description="Front-facing still facial photograph of a pet"),
    baseline_mar: float = Form(2.0, description="Baseline muzzle aspect-ratio value"),
    force_fallback: bool = Form(False, description="Force the optional Gemini vision fallback"),
):
    """Run the current four-action-unit heuristic; this is not a validated pain diagnosis."""
    if not (file.content_type or "").startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be an image.")
    try:
        image_bytes = await file.read()
        if not image_bytes:
            raise HTTPException(status_code=400, detail="Uploaded image is empty.")
        result = grimace_detector.analyze_image(
            image_bytes=image_bytes,
            baseline_mar=baseline_mar,
            force_gemini_fallback=force_fallback,
        )
        return JSONResponse(content=result)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error analyzing face photo: {exc}") from exc


@app.post("/api/incision/scan", tags=["Experimental incision comparison"])
async def scan_incision(
    day1_file: UploadFile = File(..., description="Baseline surgical-site photo"),
    dayN_file: UploadFile = File(..., description="Current surgical-site photo"),
    crop_x: Optional[int] = Form(None, description="Optional current-image bounding-box X"),
    crop_y: Optional[int] = Form(None, description="Optional current-image bounding-box Y"),
    crop_w: Optional[int] = Form(None, description="Optional current-image bounding-box width"),
    crop_h: Optional[int] = Form(None, description="Optional current-image bounding-box height"),
):
    """Compare an image pair using image-processing heuristics; not a diagnosis of infection."""
    if not (day1_file.content_type or "").startswith("image/") or not (dayN_file.content_type or "").startswith("image/"):
        raise HTTPException(status_code=400, detail="Both uploaded files must be images.")
    try:
        day1_bytes = await day1_file.read()
        dayN_bytes = await dayN_file.read()
        if not day1_bytes or not dayN_bytes:
            raise HTTPException(status_code=400, detail="Both uploaded images must be non-empty.")
        bbox = None
        if all(value is not None for value in [crop_x, crop_y, crop_w, crop_h]):
            bbox = (crop_x, crop_y, crop_w, crop_h)
        result = incision_scanner.analyze_wound_pair(
            day1_bytes=day1_bytes,
            dayN_bytes=dayN_bytes,
            dayN_bbox=bbox,
        )
        return JSONResponse(content=result)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error comparing incision photos: {exc}") from exc


# Mount after the API routes so /health and /api/... continue to resolve first.
# FastAPI serves frontend/index.html for / and its CSS/JS from this same origin.
app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
