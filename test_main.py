"""
PetTot API - Veterinary AI Vision Backend
Implements Grimace Pain Detector (FGS/CGS) and Incision Scanner (SSI/Erythema/Dehiscence).
"""

import os
from typing import Optional
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from models.Visual_Grimace_Calculator import GrimacePainDetector
from models.Incision_Change_Detection import IncisionScanner

app = FastAPI(
    title="PetTot Veterinary AI Vision API",
    description="Algorithmic Feline/Canine Grimace Pain Scale and Incision Site Infection (SSI) Scanner",
    version="1.0.0"
)

# Enable CORS for web client integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize ML model pipelines
grimace_detector = GrimacePainDetector(gemini_api_key=os.environ.get("GEMINI_API_KEY"))
incision_scanner = IncisionScanner()

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "online",
        "service": "PetTot Veterinary AI Engine",
        "models": ["Visual_Grimace_Calculator", "Incision_Change_Detection"]
    }

@app.post("/api/grimace/analyze", tags=["Grimace Pain Detector"])
async def analyze_grimace(
    file: UploadFile = File(..., description="Front-facing still facial photograph of pet"),
    baseline_mar: float = Form(2.0, description="Baseline Muzzle Aspect Ratio (default 2.0)"),
    force_fallback: bool = Form(False, description="Force Zero-Shot Gemini Flash Vision Fallback")
):
    """
    Evaluates 4 facial Action Units (Ear Position, Orbital Tightening, Muzzle Tension, Head Position)
    using keypoint geometry or Zero-Shot Gemini Fallback.
    Returns 0-8 Grimace Score and Triage status (GREEN, YELLOW, RED).
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be an image.")

    try:
        image_bytes = await file.read()
        result = grimace_detector.analyze_image(
            image_bytes=image_bytes,
            baseline_mar=baseline_mar,
            force_gemini_fallback=force_fallback
        )
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing grimace photo: {str(e)}")

@app.post("/api/incision/scan", tags=["Incision Scanner"])
async def scan_incision(
    day1_file: UploadFile = File(..., description="Day 1 Baseline surgical site photo"),
    dayN_file: UploadFile = File(..., description="Day N post-op surgical site photo"),
    crop_x: Optional[int] = Form(None, description="Optional bounding box crop X"),
    crop_y: Optional[int] = Form(None, description="Optional bounding box crop Y"),
    crop_w: Optional[int] = Form(None, description="Optional bounding box crop W"),
    crop_h: Optional[int] = Form(None, description="Optional bounding box crop H")
):
    """
    Quantitative day-over-day tracking of surgical site healing.
    Normalizes color (Gray-World) and resolution (512x512), calculates Erythema Delta (% increase in redness),
    checks for dehiscence (structural gap along suture), and produces annotated overlay mask.
    """
    if not day1_file.content_type.startswith("image/") or not dayN_file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Both uploaded files must be images.")

    try:
        day1_bytes = await day1_file.read()
        dayN_bytes = await dayN_file.read()

        bbox = None
        if all(v is not None for v in [crop_x, crop_y, crop_w, crop_h]):
            bbox = (crop_x, crop_y, crop_w, crop_h)

        result = incision_scanner.analyze_wound_pair(
            day1_bytes=day1_bytes,
            dayN_bytes=dayN_bytes,
            dayN_bbox=bbox
        )
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing incision image pair: {str(e)}")

@app.get("/", response_class=HTMLResponse, tags=["Demo Dashboard"])
async def demo_dashboard():
    """Renders interactive test dashboard UI for testing both features in browser."""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PetTot AI - Veterinary Clinical Vision Suite</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-dark: #0b0f19;
            --card-bg: rgba(22, 30, 46, 0.75);
            --card-border: rgba(255, 255, 255, 0.08);
            --accent-blue: #3b82f6;
            --accent-teal: #14b8a6;
            --accent-purple: #8b5cf6;
            --text-primary: #f3f4f6;
            --text-secondary: #9ca3af;
            --color-green: #10b981;
            --color-yellow: #f59e0b;
            --color-red: #ef4444;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Outfit', sans-serif; }

        body {
            background-color: var(--bg-dark);
            color: var(--text-primary);
            min-height: 100vh;
            background-image: 
                radial-gradient(at 15% 15%, rgba(59, 130, 246, 0.15) 0px, transparent 50%),
                radial-gradient(at 85% 85%, rgba(139, 92, 246, 0.15) 0px, transparent 50%);
            padding-bottom: 60px;
        }

        header {
            padding: 30px 40px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid var(--card-border);
            backdrop-filter: blur(12px);
        }

        .logo-group h1 {
            font-size: 26px;
            font-weight: 700;
            background: linear-gradient(135deg, #60a5fa, #a78bfa);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .logo-group p { font-size: 14px; color: var(--text-secondary); margin-top: 4px; }

        .nav-tabs {
            display: flex;
            gap: 12px;
            background: rgba(15, 23, 42, 0.6);
            padding: 6px;
            border-radius: 12px;
            border: 1px solid var(--card-border);
        }

        .tab-btn {
            background: transparent;
            border: none;
            color: var(--text-secondary);
            padding: 10px 22px;
            font-size: 15px;
            font-weight: 600;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s ease;
        }

        .tab-btn.active {
            background: linear-gradient(135deg, var(--accent-blue), var(--accent-purple));
            color: #fff;
            box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4);
        }

        main { max-width: 1280px; margin: 40px auto; padding: 0 20px; }

        .panel { display: none; }
        .panel.active { display: block; animation: fadeIn 0.4s ease-in-out; }

        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }

        .grid-container { display: grid; grid-template-columns: 1fr 1fr; gap: 30px; }

        .card {
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 20px;
            padding: 28px;
            backdrop-filter: blur(16px);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }

        .card-header {
            font-size: 20px;
            font-weight: 600;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
            border-bottom: 1px solid var(--card-border);
            padding-bottom: 12px;
        }

        .upload-dropzone {
            border: 2px dashed rgba(255, 255, 255, 0.15);
            border-radius: 14px;
            padding: 30px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s ease;
            background: rgba(255, 255, 255, 0.02);
            position: relative;
        }

        .upload-dropzone:hover {
            border-color: var(--accent-blue);
            background: rgba(59, 130, 246, 0.05);
        }

        .upload-dropzone input[type="file"] {
            position: absolute; top: 0; left: 0; width: 100%; height: 100%; opacity: 0; cursor: pointer;
        }

        .preview-img {
            max-width: 100%;
            max-height: 240px;
            border-radius: 12px;
            object-fit: cover;
            margin-top: 15px;
            border: 1px solid var(--card-border);
        }

        .btn-submit {
            width: 100%;
            padding: 14px;
            margin-top: 20px;
            background: linear-gradient(135deg, #2563eb, #7c3aed);
            border: none;
            border-radius: 12px;
            color: #fff;
            font-weight: 600;
            font-size: 16px;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 4px 20px rgba(37, 99, 235, 0.4);
        }

        .btn-submit:hover { opacity: 0.9; transform: translateY(-2px); }

        .badge-status {
            display: inline-block;
            padding: 6px 16px;
            border-radius: 30px;
            font-weight: 700;
            font-size: 14px;
            letter-spacing: 0.5px;
            margin-bottom: 15px;
        }

        .badge-GREEN { background: rgba(16, 185, 129, 0.2); color: #34d399; border: 1px solid #10b981; }
        .badge-YELLOW { background: rgba(245, 158, 11, 0.2); color: #fbbf24; border: 1px solid #f59e0b; }
        .badge-RED { background: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid #ef4444; }

        .metric-row {
            display: flex;
            justify-content: space-between;
            padding: 12px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            font-size: 15px;
        }

        .metric-label { color: var(--text-secondary); }
        .metric-value { font-family: 'JetBrains Mono', monospace; font-weight: 600; color: #60a5fa; }

        .json-box {
            background: rgba(10, 15, 26, 0.9);
            border-radius: 12px;
            padding: 15px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 13px;
            color: #a7f3d0;
            max-height: 220px;
            overflow-y: auto;
            border: 1px solid var(--card-border);
            margin-top: 15px;
        }

        .controls-group { margin-top: 15px; display: flex; flex-direction: column; gap: 10px; }
        .controls-group label { font-size: 14px; color: var(--text-secondary); }
        .controls-group input[type="range"], .controls-group input[type="checkbox"] { cursor: pointer; }
    </style>
</head>
<body>
    <header>
        <div class="logo-group">
            <h1>🐾 PetTot AI Vision Backend</h1>
            <p>Clinical Veterinary Research Engine — FGS/CGS Grimace Pain & Incision Scanner</p>
        </div>
        <nav class="nav-tabs">
            <button class="tab-btn active" onclick="switchTab('grimace')">1. Grimace Pain Detector</button>
            <button class="tab-btn" onclick="switchTab('incision')">2. Incision Scanner</button>
        </nav>
    </header>

    <main>
        <!-- Panel 1: Grimace Pain Detector -->
        <section id="panel-grimace" class="panel active">
            <div class="grid-container">
                <div class="card">
                    <div class="card-header">📷 Input Facial Photograph</div>
                    <form id="form-grimace" onsubmit="submitGrimace(event)">
                        <div class="upload-dropzone" id="grimace-dropzone">
                            <p>📸 Click or Drag Front-Facing Pet Photo Here</p>
                            <input type="file" id="grimace-file" accept="image/*" required onchange="previewFile(this, 'grimace-preview')">
                        </div>
                        <img id="grimace-preview" class="preview-img" style="display:none;">

                        <div class="controls-group">
                            <label>Baseline Muzzle Aspect Ratio (MAR): <span id="mar-val">2.0</span></label>
                            <input type="range" min="1.0" max="3.5" step="0.1" value="2.0" oninput="document.getElementById('mar-val').innerText = this.value; document.getElementById('mar-input').value = this.value;">
                            <input type="hidden" id="mar-input" name="baseline_mar" value="2.0">

                            <label style="display: flex; align-items: center; gap: 8px; margin-top: 10px;">
                                <input type="checkbox" id="force-fallback"> Force Zero-Shot Gemini Flash Vision Fallback
                            </label>
                        </div>

                        <button type="submit" class="btn-submit" id="btn-grimace">Analyze Grimace Scale (FGS/CGS)</button>
                    </form>
                </div>

                <div class="card">
                    <div class="card-header">📊 Clinical Triage & Metric Output</div>
                    <div id="grimace-output">
                        <p style="color: var(--text-secondary);">Upload a front-facing facial photo and click Analyze to view Action Unit breakdown and triage rating.</p>
                    </div>
                </div>
            </div>
        </section>

        <!-- Panel 2: Incision Scanner -->
        <section id="panel-incision" class="panel">
            <div class="grid-container">
                <div class="card">
                    <div class="card-header">🩹 Day-over-Day Surgical Site Photos</div>
                    <form id="form-incision" onsubmit="submitIncision(event)">
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                            <div>
                                <label style="font-size: 13px; color: var(--text-secondary); margin-bottom: 6px; display: block;">Day 1 Baseline Photo</label>
                                <div class="upload-dropzone">
                                    <p>📁 Day 1 Image</p>
                                    <input type="file" id="day1-file" accept="image/*" required onchange="previewFile(this, 'day1-preview')">
                                </div>
                                <img id="day1-preview" class="preview-img" style="display:none;">
                            </div>
                            <div>
                                <label style="font-size: 13px; color: var(--text-secondary); margin-bottom: 6px; display: block;">Day N Post-Op Photo</label>
                                <div class="upload-dropzone">
                                    <p>📁 Day N Image</p>
                                    <input type="file" id="dayN-file" accept="image/*" required onchange="previewFile(this, 'dayN-preview')">
                                </div>
                                <img id="dayN-preview" class="preview-img" style="display:none;">
                            </div>
                        </div>

                        <button type="submit" class="btn-submit" id="btn-incision">Run Incision Change & SSI Scan</button>
                    </form>
                </div>

                <div class="card">
                    <div class="card-header">🔍 Healing Assessment & Overlay Mask</div>
                    <div id="incision-output">
                        <p style="color: var(--text-secondary);">Upload Day 1 Baseline and Day N photos to evaluate Erythema Delta (% change in redness) and dehiscence.</p>
                    </div>
                </div>
            </div>
        </section>
    </main>

    <script>
        function switchTab(tab) {
            document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
            document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));

            if (tab === 'grimace') {
                event.target.classList.add('active');
                document.getElementById('panel-grimace').classList.add('active');
            } else {
                event.target.classList.add('active');
                document.getElementById('panel-incision').classList.add('active');
            }
        }

        function previewFile(input, imgId) {
            const file = input.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    const img = document.getElementById(imgId);
                    img.src = e.target.result;
                    img.style.display = 'block';
                };
                reader.readAsDataURL(file);
            }
        }

        async function submitGrimace(e) {
            e.preventDefault();
            const btn = document.getElementById('btn-grimace');
            const outputDiv = document.getElementById('grimace-output');
            const fileInput = document.getElementById('grimace-file');

            if (!fileInput.files[0]) return;

            btn.disabled = true;
            btn.innerText = "Processing Facial Keypoints & Vision Pipeline...";
            outputDiv.innerHTML = "<p style='color: #60a5fa;'>Extracting 35 facial keypoints & scoring Action Units...</p>";

            const formData = new FormData();
            formData.append('file', fileInput.files[0]);
            formData.append('baseline_mar', document.getElementById('mar-input').value);
            formData.append('force_fallback', document.getElementById('force-fallback').checked);

            try {
                const res = await fetch('/api/grimace/analyze', { method: 'POST', body: formData });
                const data = await res.json();

                btn.disabled = false;
                btn.innerText = "Analyze Grimace Scale (FGS/CGS)";

                if (!res.ok) throw new Error(data.detail || "Grimace analysis error");

                const aus = data.action_units;
                const metrics = data.metrics;

                outputDiv.innerHTML = `
                    <div class="badge-status badge-${data.triage_color}">
                        ${data.triage_color}: Total Score ${data.total_grimace_score} / ${data.max_score}
                    </div>
                    <p style="margin-bottom: 15px; font-weight: 500;">${data.triage_status}</p>

                    <div class="metric-row"><span class="metric-label">Pipeline:</span><span class="metric-value">${data.pipeline}</span></div>
                    <div class="metric-row"><span class="metric-label">Confidence:</span><span class="metric-value">${(data.confidence_score * 100).toFixed(1)}%</span></div>
                    
                    <div class="metric-row"><span class="metric-label">AU1 Ear Position Score:</span><span class="metric-value">${aus.ear_position_au1}</span></div>
                    <div class="metric-row"><span class="metric-label">AU2 Orbital Tightening Score:</span><span class="metric-value">${aus.orbital_tightening_au2}</span></div>
                    <div class="metric-row"><span class="metric-label">AU3 Muzzle Tension Score:</span><span class="metric-value">${aus.muzzle_tension_au3}</span></div>
                    <div class="metric-row"><span class="metric-label">AU4 Head Position Score:</span><span class="metric-value">${aus.head_position_au4}</span></div>

                    ${metrics.ear_aspect_ratio !== null ? `
                        <div class="metric-row"><span class="metric-label">Eye Aspect Ratio (EAR):</span><span class="metric-value">${metrics.ear_aspect_ratio}</span></div>
                        <div class="metric-row"><span class="metric-label">Ear Angle Vector (θ_ear):</span><span class="metric-value">${metrics.ear_angle_degrees}°</span></div>
                        <div class="metric-row"><span class="metric-label">Muzzle Aspect Ratio (MAR):</span><span class="metric-value">${metrics.muzzle_aspect_ratio}</span></div>
                    ` : ''}

                    <div style="margin-top: 15px;">
                        <span style="font-size: 13px; color: var(--text-secondary);">Landmark Alignment Preview:</span>
                        <img src="${data.visualization_b64}" class="preview-img" style="margin-top: 5px;">
                    </div>
                `;
            } catch (err) {
                btn.disabled = false;
                btn.innerText = "Analyze Grimace Scale (FGS/CGS)";
                outputDiv.innerHTML = `<p style="color: #ef4444;">Error: ${err.message}</p>`;
            }
        }

        async function submitIncision(e) {
            e.preventDefault();
            const btn = document.getElementById('btn-incision');
            const outputDiv = document.getElementById('incision-output');
            const day1 = document.getElementById('day1-file');
            const dayN = document.getElementById('dayN-file');

            if (!day1.files[0] || !dayN.files[0]) return;

            btn.disabled = true;
            btn.innerText = "Running Pre-Processing & HSV Segmentation...";
            outputDiv.innerHTML = "<p style='color: #60a5fa;'>Executing Gray-World normalization & HSV Sobel wound segmentation...</p>";

            const formData = new FormData();
            formData.append('day1_file', day1.files[0]);
            formData.append('dayN_file', dayN.files[0]);

            try {
                const res = await fetch('/api/incision/scan', { method: 'POST', body: formData });
                const data = await res.json();

                btn.disabled = false;
                btn.innerText = "Run Incision Change & SSI Scan";

                if (!res.ok) throw new Error(data.detail || "Incision scan error");

                const m = data.metrics;

                outputDiv.innerHTML = `
                    <div class="badge-status badge-${data.triage_color}">
                        ${data.triage_color}: ${data.triage_label}
                    </div>
                    <p style="margin-bottom: 15px; font-weight: 500;">${data.action_recommendation}</p>

                    <div class="metric-row"><span class="metric-label">Day 1 Redness Ratio (E_base):</span><span class="metric-value">${m.day1_erythema_ratio_e_base}%</span></div>
                    <div class="metric-row"><span class="metric-label">Day N Redness Ratio (E_current):</span><span class="metric-value">${m.dayN_erythema_ratio_e_current}%</span></div>
                    <div class="metric-row"><span class="metric-label">Erythema Change (ΔE):</span><span class="metric-value" style="color:${m.delta_e_percent >= 20 ? '#ef4444' : '#34d399'};">${m.delta_e_percent >= 0 ? '+' : ''}${m.delta_e_percent}%</span></div>
                    <div class="metric-row"><span class="metric-label">Structural Gap (Dehiscence):</span><span class="metric-value">${m.structural_gap_detected ? '🚨 DETECTED' : '✅ None'}</span></div>
                    ${m.max_gap_size_px > 0 ? `<div class="metric-row"><span class="metric-label">Max Gap Size:</span><span class="metric-value">${m.max_gap_size_px}px</span></div>` : ''}

                    <div style="margin-top: 15px;">
                        <span style="font-size: 13px; color: var(--text-secondary);">Annotated Incision Overlay Mask:</span>
                        <img src="${data.overlay_mask_b64}" class="preview-img" style="margin-top: 5px;">
                    </div>
                `;
            } catch (err) {
                btn.disabled = false;
                btn.innerText = "Run Incision Change & SSI Scan";
                outputDiv.innerHTML = `<p style="color: #ef4444;">Error: ${err.message}</p>`;
            }
        }
    </script>
</body>
</html>
    """
