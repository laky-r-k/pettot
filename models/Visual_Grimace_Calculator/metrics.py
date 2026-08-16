"""
Grimace Pain Metric & AU Classifier Module
Calculates EAR, Ear Angle, MAR, Head Position, discrete AU scores, total score, and triage status.
"""

import math
import numpy as np
from typing import Dict, Any, Tuple

def calculate_distance(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    """Euclidean distance between two 2D points."""
    return float(np.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2))

def calculate_ear(eye_pts: list) -> float:
    """
    Calculate Eye Aspect Ratio (EAR) based on 6 eye landmark points:
    EAR = (||p2 - p6|| + ||p3 - p5||) / (2 * ||p1 - p4||)
    """
    if len(eye_pts) < 6:
        return 0.30  # Default normal

    p1, p2, p3, p4, p5, p6 = eye_pts[:6]
    v1 = calculate_distance(p2, p6)
    v2 = calculate_distance(p3, p5)
    horiz = calculate_distance(p1, p4)

    if horiz < 1e-6:
        return 0.30

    ear = (v1 + v2) / (2.0 * horiz)
    return float(ear)

def calculate_ear_angle(left_ear_tip: Tuple[float, float], 
                        right_ear_tip: Tuple[float, float], 
                        inter_ocular_center: Tuple[float, float]) -> float:
    """
    Calculate Ear Angle Vector (theta_ear):
    Calculates the inner angle formed between ear tip keypoints (E_L, E_R) and the inter-ocular center (C).
    Wider angle relative to baseline indicates outward ear flattening.
    """
    # Vectors from center C to left ear tip and right ear tip
    v_l = np.array([left_ear_tip[0] - inter_ocular_center[0], left_ear_tip[1] - inter_ocular_center[1]])
    v_r = np.array([right_ear_tip[0] - inter_ocular_center[0], right_ear_tip[1] - inter_ocular_center[1]])

    norm_l = np.linalg.norm(v_l)
    norm_r = np.linalg.norm(v_r)

    if norm_l < 1e-6 or norm_r < 1e-6:
        return 25.0

    cosine_angle = np.dot(v_l, v_r) / (norm_l * norm_r)
    cosine_angle = np.clip(cosine_angle, -1.0, 1.0)
    angle_deg = np.degrees(np.arccos(cosine_angle))
    
    # We measure deviation from vertical / horizontal flattening: angle theta_ear
    return float(angle_deg)

def calculate_mar(muzzle_polygon: list) -> float:
    """
    Calculate Muzzle Aspect Ratio (MAR):
    Width-to-height ratio of muzzle bounding polygon.
    """
    if not muzzle_polygon or len(muzzle_polygon) < 4:
        return 2.0  # Baseline normal MAR

    pts = np.array(muzzle_polygon)
    min_x, max_x = np.min(pts[:, 0]), np.max(pts[:, 0])
    min_y, max_y = np.min(pts[:, 1]), np.max(pts[:, 1])

    width = max_x - min_x
    height = max_y - min_y

    if height < 1e-6:
        return 2.0

    return float(width / height)

def score_ear(ear_val: float) -> int:
    """
    AU2 Orbital Tightening:
    > 0.28 -> Score 0 (Normal)
    0.18 - 0.28 -> Score 1 (Moderate)
    < 0.18 -> Score 2 (Severe)
    """
    if ear_val > 0.28:
        return 0
    elif ear_val >= 0.18:
        return 1
    else:
        return 2

def score_ear_angle(angle_deg: float) -> int:
    """
    AU1 Ear Position:
    < 35 deg -> Score 0 (Normal)
    35 - 60 deg -> Score 1 (Moderate)
    > 60 deg -> Score 2 (Severe)
    """
    if angle_deg < 35.0:
        return 0
    elif angle_deg <= 60.0:
        return 1
    else:
        return 2

def score_mar(mar_val: float, baseline_mar: float = 2.0) -> int:
    """
    AU3 Muzzle Tension:
    Baseline +- 5% -> Score 0
    Baseline +6% to +15% -> Score 1
    Baseline > +15% -> Score 2
    """
    pct_change = ((mar_val - baseline_mar) / baseline_mar) * 100.0
    if pct_change <= 5.0:
        return 0
    elif pct_change <= 15.0:
        return 1
    else:
        return 2

def score_head_position(head_drop_ratio: float) -> int:
    """
    AU4 Head Position:
    Evaluates head drop below shoulder/spine line.
    head_drop_ratio <= 0.10 -> Score 0 (Normal)
    0.10 < ratio <= 0.25 -> Score 1 (Moderate drop)
    ratio > 0.25 -> Score 2 (Severe drop)
    """
    if head_drop_ratio <= 0.10:
        return 0
    elif head_drop_ratio <= 0.25:
        return 1
    else:
        return 2

def evaluate_grimace_score(
    ear_val: float, 
    ear_angle: float, 
    mar_val: float, 
    head_drop_ratio: float = 0.0,
    baseline_mar: float = 2.0
) -> Dict[str, Any]:
    """
    Computes total grimace score and assigns clinical triage classification.
    """
    au1_score = score_ear_angle(ear_angle)
    au2_score = score_ear(ear_val)
    au3_score = score_mar(mar_val, baseline_mar)
    au4_score = score_head_position(head_drop_ratio)

    total_score = au1_score + au2_score + au3_score + au4_score

    if total_score <= 2:
        triage_color = "GREEN"
        triage_status = "Normal post-operative status"
    elif total_score <= 4:
        triage_color = "YELLOW"
        triage_status = "Moderate pain; flagged for 12-hour observation"
    else:
        triage_color = "RED"
        triage_status = "Severe acute pain; immediate triage flag raised"

    return {
        "action_units": {
            "ear_position_au1": au1_score,
            "orbital_tightening_au2": au2_score,
            "muzzle_tension_au3": au3_score,
            "head_position_au4": au4_score
        },
        "metrics": {
            "ear_aspect_ratio": round(ear_val, 4),
            "ear_angle_degrees": round(ear_angle, 2),
            "muzzle_aspect_ratio": round(mar_val, 4),
            "head_drop_ratio": round(head_drop_ratio, 4)
        },
        "total_grimace_score": total_score,
        "max_score": 8,
        "triage_color": triage_color,
        "triage_status": triage_status
    }
