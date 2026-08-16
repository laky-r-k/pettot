"""
Incision Scanner Pipeline Coordinator
Tracks surgical site healing day-over-day, identifying SSI, erythema delta, and dehiscence.
"""

import cv2
import base64
import numpy as np
from typing import Dict, Any, Optional, Tuple

from .preprocessor import ImagePreprocessor
from .erythema_segmenter import ErythemaSegmenter
from .dehiscence_detector import DehiscenceDetector

class IncisionScanner:
    """
    Main Incision Scanner service.
    Evaluates Day 1 Baseline vs Day N image pairs.
    """

    def __init__(self):
        self.preprocessor = ImagePreprocessor(target_size=(512, 512), border_expansion=0.20)
        self.erythema_segmenter = ErythemaSegmenter(buffer_radius=15, sat_min=50, val_min=40)
        self.dehiscence_detector = DehiscenceDetector(gap_threshold_px=18)

    def analyze_wound_pair(
        self,
        day1_bytes: bytes,
        dayN_bytes: bytes,
        day1_bbox: Optional[Tuple[int, int, int, int]] = None,
        dayN_bbox: Optional[Tuple[int, int, int, int]] = None
    ) -> Dict[str, Any]:
        """
        Processes Day 1 Baseline vs Day N photo pair and returns healing assessment, delta E, and overlay.
        """
        # Decode Day 1 and Day N image bytes
        arr1 = np.frombuffer(day1_bytes, np.uint8)
        arrN = np.frombuffer(dayN_bytes, np.uint8)

        img1_raw = cv2.imdecode(arr1, cv2.IMREAD_COLOR)
        imgN_raw = cv2.imdecode(arrN, cv2.IMREAD_COLOR)

        if img1_raw is None or imgN_raw is None:
            raise ValueError("Failed to decode one or both input image files.")

        # Step 1: Pre-Processing & Alignment Pipeline
        img1_norm = self.preprocessor.process(img1_raw, day1_bbox)
        imgN_norm = self.preprocessor.process(imgN_raw, dayN_bbox)

        # Step 2: HSV Erythema Segmentation
        res_day1 = self.erythema_segmenter.calculate_erythema_pixel_ratio(img1_norm)
        res_dayN = self.erythema_segmenter.calculate_erythema_pixel_ratio(imgN_norm)

        e_base = res_day1["erythema_ratio_er"]
        e_current = res_dayN["erythema_ratio_er"]

        # Step 3: Delta Comparison Engine
        denom = max(e_base, 0.1)
        delta_e = ((e_current - e_base) / denom) * 100.0

        # Step 4: Dehiscence / Structural Gap Detection on Day N
        dehiscence_res = self.dehiscence_detector.detect_dehiscence(imgN_norm, res_dayN["m_wound"])
        gap_detected = dehiscence_res["dehiscence_detected"]

        # Step 5: Triage Matrix Assignment
        if gap_detected or delta_e >= 50.0:
            triage_color = "RED"
            triage_label = "Urgent Triage (Suspected SSI / Dehiscence)"
            action_recommendation = "Escalated to veterinary dashboard immediately. Overlay mask generated."
        elif delta_e >= 20.0:
            triage_color = "YELLOW"
            triage_label = "Watchlist Flag (Minor Inflammation)"
            action_recommendation = "Moderate redness increase (+20% to +50%). Request updated photo in 12 hours."
        else:
            triage_color = "GREEN"
            triage_label = "On Track (Normal Healing)"
            action_recommendation = "Surgical site healing on track. Erythema stable or decreasing. Suture line intact."

        # Step 6: Generate Visualization Overlay Mask
        overlay_b64 = self._generate_overlay_mask(
            imgN_norm=imgN_norm,
            m_wound=res_dayN["m_wound"],
            red_mask=res_dayN["red_in_wound_mask"],
            triage_color=triage_color,
            delta_e=delta_e,
            gap_detected=gap_detected,
            gap_boxes=dehiscence_res.get("gap_boxes", [])
        )

        return {
            "triage_color": triage_color,
            "triage_label": triage_label,
            "action_recommendation": action_recommendation,
            "metrics": {
                "day1_erythema_ratio_e_base": round(e_base, 2),
                "dayN_erythema_ratio_e_current": round(e_current, 2),
                "delta_e_percent": round(delta_e, 2),
                "structural_gap_detected": gap_detected,
                "max_gap_size_px": dehiscence_res.get("max_gap_size_px", 0.0)
            },
            "day1_summary": {
                "total_wound_pixels": res_day1["total_wound_pixels"],
                "red_wound_pixels": res_day1["red_wound_pixels"]
            },
            "dayN_summary": {
                "total_wound_pixels": res_dayN["total_wound_pixels"],
                "red_wound_pixels": res_dayN["red_wound_pixels"]
            },
            "overlay_mask_b64": overlay_b64
        }

    def _generate_overlay_mask(
        self,
        imgN_norm: np.ndarray,
        m_wound: np.ndarray,
        red_mask: np.ndarray,
        triage_color: str,
        delta_e: float,
        gap_detected: bool,
        gap_boxes: list
    ) -> str:
        """Generates an annotated overlay image with wound boundaries, erythema, and status."""
        overlay = imgN_norm.copy()

        # Highlight wound buffer area in cyan contour
        contours, _ = cv2.findContours(m_wound, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(overlay, contours, -1, (255, 255, 0), 2)

        # Highlight red inflamed pixels in bright red semi-transparent overlay
        red_overlay = overlay.copy()
        red_overlay[red_mask > 0] = [0, 0, 255]
        cv2.addWeighted(red_overlay, 0.45, overlay, 0.55, 0, overlay)

        # Draw warning box for structural gaps / dehiscence
        for box in gap_boxes:
            x, y, w, h = box
            cv2.rectangle(overlay, (x, y), (x + w, y + h), (0, 0, 255), 2)
            cv2.putText(overlay, "DEHISCENCE GAP", (x, max(15, y - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)

        # Status Banner Header
        banner_color = (0, 200, 0) if triage_color == "GREEN" else ((0, 215, 255) if triage_color == "YELLOW" else (0, 0, 230))
        cv2.rectangle(overlay, (0, 0), (512, 45), banner_color, -1)
        
        status_text = f"TRIAGE: {triage_color} | dE: {delta_e:+.1f}%"
        if gap_detected:
            status_text += " | STRUCTURAL GAP DETECTED"

        cv2.putText(overlay, status_text, (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        # Encode overlay to Base64 JPEG
        _, buffer = cv2.imencode('.jpg', overlay)
        b64_str = base64.b64encode(buffer).decode('utf-8')
        return f"data:image/jpeg;base64,{b64_str}"
