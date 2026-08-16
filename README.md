# 🐾 PetTot AI - Veterinary Clinical Vision Engine

PetTot AI is an advanced veterinary clinical vision backend built with **FastAPI**, **OpenCV**, **MediaPipe**, and **Google Gemini 2.5 Flash Vision**. It translates validated veterinary clinical research into objective, real-time algorithmic scoring and automated triage.

---

## 🌟 Key Features

### 1. 🐱🐶 Grimace Pain Detector (`models/Visual_Grimace_Calculator/`)
Translates validated veterinary clinical research—specifically the **Feline Grimace Scale (FGS)** and **Canine Grimace Scale (CGS)**—into objective algorithmic pain scoring.

* **Face Alignment & Landmark Detection**: Crops and normalizes head pose using 35 facial keypoints mapping eyes, ears, nose tip, and muzzle perimeter.
* **Geometric Feature Calculations**:
  * **Eye Aspect Ratio ($EAR$)**: Quantifies orbital tightening by measuring vertical eye opening against horizontal width:
    $$EAR = \frac{\|p_2 - p_6\| + \|p_3 - p_5\|}{2 \|p_1 - p_4\|}$$
    * $> 0.28 \implies \text{Score } 0$ (Normal)
    * $0.18 - 0.28 \implies \text{Score } 1$ (Moderate Squint)
    * $< 0.18 \implies \text{Score } 2$ (Severe Tightening)
  * **Ear Angle Vector ($\theta_{ear}$)**: Inner angle formed between ear tip keypoints ($E_L, E_R$) and inter-ocular center line ($C$).
    * $< 35^\circ \implies \text{Score } 0$ (Normal)
    * $35^\circ - 60^\circ \implies \text{Score } 1$ (Moderate Flattening)
    * $> 60^\circ \implies \text{Score } 2$ (Severe Outward Rotation)
  * **Muzzle Aspect Ratio ($MAR$)**: Width-to-height ratio of muzzle bounding polygon. Increased tension causes horizontal compression ($MAR$ increases).
    * Baseline $\pm 5\% \implies \text{Score } 0$
    * Baseline $+6\%$ to $+15\% \implies \text{Score } 1$
    * Baseline $> +15\% \implies \text{Score } 2$
  * **Head Position Score (AU4)**: Evaluates head drop below shoulder/spine line.
* **Total Grimace Score**:
  $$\text{Total Grimace Score} = \sum_{i=1}^4 \text{AU}_i \quad (\text{Max Score } 8)$$
  * 🟢 **Score 0–2 (Green)**: Normal post-operative status.
  * 🟡 **Score 3–4 (Yellow)**: Moderate pain; flagged for 12-hour observation.
  * 🔴 **Score 5–8 (Red)**: Severe acute pain; immediate triage flag raised.
* **Zero-Shot Fallback Pipeline (Gemini Flash Vision)**: Automatically engages when keypoint landmark detection confidence is low or lighting is poor, leveraging a structured JSON schema constraint via Gemini 2.5 Flash.

---

### 2. 🩹 Incision Scanner (`models/Incision_Change_Detection/`)
Quantitatively tracks surgical site healing, identifying early **Surgical Site Infections (SSI)**, localized swelling, and wound opening (**dehiscence**) by evaluating day-over-day image pairs (Day 1 Baseline vs. Day $N$).

* **Pre-Processing & Alignment Pipeline**:
  * **Bounding Box Crop**: Crops surgical region with a 20% outer border buffer.
  * **Gray-World Color Normalization**: Corrects home lighting color casts (warm incandescent vs. cool daylight) by scaling color channels to an average gray value ($\mu_R = \mu_G = \mu_B$).
  * **Spatial Scale Normalization**: Resizes images to standard $512 \times 512\text{px}$.
* **Infection & Erythema Detection via HSV Segmentation**:
  * **Incision Line Isolation (Sobel Edge Mask)**: Applies Sobel gradient filtering to identify suture lines, creating a dilated binary mask ($M_{\text{wound}}$) representing primary incision site + 15-pixel radius surrounding buffer.
  * **Erythema Segmentation Thresholds**: Isolates red/pink hue spectrums associated with inflammation:
    * Hue Range 1: $0^\circ \le H \le 12^\circ$ (Deep Reds / Active Inflammation)
    * Hue Range 2: $165^\circ \le H \le 180^\circ$ (Magenta-Reds)
    * Saturation Filter: $S \ge 50$ (filters out normal skin tones)
  * **Erythema Pixel Ratio ($E_r$)**:
    $$E_r = \left( \frac{\sum P_{\text{red}} \cap M_{\text{wound}}}{\sum P_{\text{total}} \cap M_{\text{wound}}} \right) \times 100$$
* **Delta Comparison Engine ($\Delta E$)**:
  $$\Delta E = \left( \frac{E_{\text{current}} - E_{\text{base}}}{\max(E_{\text{base}}, 0.1)} \right) \times 100$$
* **Dehiscence & Gap Detection**: Evaluates suture line continuity. Structural gaps or openings along the incision line automatically trigger an urgent triage flag.
* **Triage Matrix**:
  * 🟢 **Green (On Track)**: $\Delta E < +20\%$. Erythema stable or decreasing. Suture line intact.
  * 🟡 **Yellow (Watchlist Flag)**: $+20\% \le \Delta E < +50\%$. Moderate redness increase. Triggers request for updated photo in 12 hours.
  * 🔴 **Red (Urgent Triage)**: $\Delta E \ge +50\%$ OR structural gap detected along suture contour. Escalates to veterinary dashboard with an annotated overlay mask.

---

## 📁 Repository Structure

```
pettot/
├── main.py                            # FastAPI application server & interactive HTML test UI
├── models/
│   ├── Visual_Grimace_Calculator/     # Grimace Pain Detector model package
│   │   ├── __init__.py
│   │   ├── landmark_extractor.py     # 35-keypoint landmark detection & pose crop
│   │   ├── metrics.py                # EAR, Ear Angle, MAR & AU classification logic
│   │   ├── gemini_fallback.py        # Zero-shot Gemini Flash Vision fallback integration
│   │   └── grimace_detector.py       # Main Grimace Pain Detector coordinator
│   └── Incision_Change_Detection/    # Incision Scanner model package
│       ├── __init__.py
│       ├── preprocessor.py           # 20% border crop, Gray-World, 512x512 resize
│       ├── erythema_segmenter.py     # Sobel M_wound (15px buffer) & HSV red segmentation
│       ├── dehiscence_detector.py    # Structural gap & wound opening detector
│       └── incision_scanner.py       # Day 1 vs Day N delta engine & overlay generator
└── README.md                          # Project documentation
```

---

## 🛠️ Quick Start & Installation

### 1. Requirements
* Python 3.10+
* Dependencies: `fastapi`, `uvicorn`, `opencv-python`, `numpy`, `mediapipe`, `google-genai`, `pillow`

### 2. Installation

```bash
# Clone the repository
git clone https://github.com/your-username/pettot.git
cd pettot

# Install dependencies from requirements.txt
pip install -r requirements.txt
```

### 3. Running the FastAPI Application

```bash
# Start FastAPI backend with hot-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

* **Interactive Web Dashboard**: Navigate to [`http://localhost:8000/`](http://localhost:8000/) in your browser to upload photos and test both features live!
* **Swagger API Documentation**: Navigate to [`http://localhost:8000/docs`](http://localhost:8000/docs) for full interactive API specs.

---

## 📡 API Endpoints Summary

### `POST /api/grimace/analyze`
Evaluates facial photograph for Grimace Pain score.

* **Form Data**:
  * `file`: (Image file) Front-facing pet facial photo.
  * `baseline_mar`: (float, default `2.0`) Baseline Muzzle Aspect Ratio.
  * `force_fallback`: (bool, default `false`) Force zero-shot Gemini Vision fallback.
* **Returns**: JSON object with Action Unit scores, metrics, total score (0-8), triage color (`GREEN`, `YELLOW`, `RED`), and Base64 visual alignment preview.

### `POST /api/incision/scan`
Evaluates Day 1 Baseline vs Day N surgical site photo pair.

* **Form Data**:
  * `day1_file`: (Image file) Day 1 Baseline surgical photo.
  * `dayN_file`: (Image file) Day N Post-Op surgical photo.
  * `crop_x`, `crop_y`, `crop_w`, `crop_h`: (Optional ints) Bounding box coordinates.
* **Returns**: JSON object with $E_{\text{base}}$, $E_{\text{current}}$, $\Delta E\%$, dehiscence detection flag, triage recommendation, and Base64 annotated overlay mask.

---

## 📜 License
Developed for Veterinary AI Triage & Clinical Monitoring.
