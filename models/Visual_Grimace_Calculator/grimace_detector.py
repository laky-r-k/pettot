"""
Grimace Pain Detector - Main Pipeline Coordinator
Translates veterinary clinical research (FGS & CGS) into algorithmic scoring.
"""

import cv2
import base64
import numpy as np
from typing import Dict, Any, Optional

from .landmark_extractor import LandmarkExtractor
from .metrics import (
    calculate_ear,
    calculate_ear_angle,
    calculate_mar,
    evaluate_grimace_score
)
from .gemini_fallback import GeminiGrimaceFallback

class GrimacePainDetector:
    """
    Main Grimace Pain Detector service.
    Evaluates 4 Action Units: Ear Position (AU1), Orbital Tightening (AU2), Muzzle Tension (AU3), Head Position (AU4).
    """

    def __init__(self, gemini_api_key: Optional[str] = None):
        self.landmark_extractor = LandmarkExtractor()
        self.gemini_fallback = GeminiGrimaceFallback(api_key=gemini_api_key)

    def analyze_image(
        self, 
        image_bytes: bytes, 
        baseline_mar: float = 2.0, 
        force_gemini_fallback: bool = False
    ) -> Dict[str, Any]:
        """
        Analyze facial photo bytes and return Grimace Pain assessment score and triage report.
        """
        # Decode image bytes to OpenCV BGR numpy array
        np_arr = np.frombuffer(image_bytes, np.uint8)
        image_bgr = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        if image_bgr is None:
            raise ValueError("Invalid image file or format could not be decoded.")

        # If forced fallback requested, jump directly to Gemini Vision / Zero-shot
        if force_gemini_fallback:
            return self._run_zero_shot_pipeline(image_bgr, reason="User forced zero-shot fallback.")

        # Step 1: Landmark Detection & Face Alignment
        landmark_res = self.landmark_extractor.extract_landmarks(image_bgr)

        # If landmark extraction succeeded with good confidence
        if landmark_res["success"] and landmark_res["confidence"] >= 0.50:
            left_eye = landmark_res["left_eye_pts"]
            right_eye = landmark_res["right_eye_pts"]

            # Calculate EAR (average of left & right eye if available)
            ear_l = calculate_ear(left_eye) if left_eye else 0.30
            ear_r = calculate_ear(right_eye) if right_eye else 0.30
            avg_ear = (ear_l + ear_r) / 2.0

            # Calculate Ear Angle Vector theta_ear
            theta_ear = calculate_ear_angle(
                landmark_res["left_ear_tip"],
                landmark_res["right_ear_tip"],
                landmark_res["inter_ocular_center"]
            )

            # Calculate MAR
            mar_val = calculate_mar(landmark_res["muzzle_polygon"])

            # Head drop ratio
            head_drop = landmark_res.get("head_drop_ratio", 0.0)

            # Score Action Units & compute total score
            scoring = evaluate_grimace_score(
                ear_val=avg_ear,
                ear_angle=theta_ear,
                mar_val=mar_val,
                head_drop_ratio=head_drop,
                baseline_mar=baseline_mar
            )

            # Encode annotated image to Base64 JPEG
            annotated_img = landmark_res["annotated_image"]
            _, buffer = cv2.imencode('.jpg', annotated_img)
            b64_img = base64.b64encode(buffer).decode('utf-8')

            return {
                "pipeline": "Geometric Vision Keypoints (FGS/CGS)",
                "confidence_score": landmark_res["confidence"],
                "total_grimace_score": scoring["total_grimace_score"],
                "max_score": 8,
                "triage_color": scoring["triage_color"],
                "triage_status": scoring["triage_status"],
                "action_units": scoring["action_units"],
                "metrics": scoring["metrics"],
                "visualization_b64": f"data:image/jpeg;base64,{b64_img}"
            }
        else:
            # Step 2: Zero-Shot Fallback Pipeline (Gemini Flash Vision)
            return self._run_zero_shot_pipeline(
                image_bgr, 
                reason="Facial keypoint landmark extraction low confidence or failed."
            )

    def _run_zero_shot_pipeline(self, image_bgr: np.ndarray, reason: str) -> Dict[str, Any]:
        """Runs the Gemini Vision fallback pipeline."""
        fb_result = self.gemini_fallback.analyze_fallback(image_bgr)
        aus = fb_result["action_units"]

        au1 = aus.get("ear_position_au1", 0)
        au2 = aus.get("orbital_tightening_au2", 0)
        au3 = aus.get("muzzle_tension_au3", 0)
        au4 = aus.get("head_position_au4", 0)

        total_score = au1 + au2 + au3 + au4

        if total_score <= 2:
            triage_color = "GREEN"
            triage_status = "Normal post-operative status"
        elif total_score <= 4:
            triage_color = "YELLOW"
            triage_status = "Moderate pain; flagged for 12-hour observation"
        else:
            triage_color = "RED"
            triage_status = "Severe acute pain; immediate triage flag raised"

        # Encode image to Base64 JPEG for visualization
        annotated_img = image_bgr.copy()
        cv2.putText(
            annotated_img, 
            f"Zero-Shot Fallback ({triage_color}) Score: {total_score}/8", 
            (20, 40), 
            cv2.FONT_HERSHEY_SIMPLEX, 
            0.7, 
            (0, 0, 255) if triage_color == "RED" else (0, 255, 255), 
            2
        )
        _, buffer = cv2.imencode('.jpg', annotated_img)
        b64_img = base64.b64encode(buffer).decode('utf-8')

        return {
            "pipeline": f"Zero-Shot Fallback ({fb_result.get('source', 'Gemini Vision')})",
            "fallback_reason": reason,
            "confidence_score": fb_result.get("confidence_score", 0.8),
            "total_grimace_score": total_score,
            "max_score": 8,
            "triage_color": triage_color,
            "triage_status": triage_status,
            "action_units": {
                "ear_position_au1": au1,
                "orbital_tightening_au2": au2,
                "muzzle_tension_au3": au3,
                "head_position_au4": au4
            },
            "metrics": {
                "ear_aspect_ratio": None,
                "ear_angle_degrees": None,
                "muzzle_aspect_ratio": None,
                "head_drop_ratio": None
            },
            "visualization_b64": f"data:image/jpeg;base64,{b64_img}"
        }
