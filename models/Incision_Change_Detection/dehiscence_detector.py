"""
Structural Gap & Dehiscence Detector
Detects wound opening, dehiscence, or suture contour gaps along the primary incision line.
"""

import cv2
import numpy as np
from typing import Dict, Any, List

class DehiscenceDetector:
    def __init__(self, gap_threshold_px: int = 18):
        self.gap_threshold_px = gap_threshold_px

    def detect_dehiscence(self, image_bgr: np.ndarray, m_wound: np.ndarray) -> Dict[str, Any]:
        """
        Analyzes incision site for wound opening or structural gap along suture contour.
        Returns gap detection status, maximum gap size, and gap location bounding boxes.
        """
        gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Sobel edge detection to find fine suture contours
        edges = cv2.Canny(blurred, 30, 100)
        incision_edges = cv2.bitwise_and(edges, edges, mask=m_wound)

        # Find contours of incision edges
        contours, _ = cv2.findContours(incision_edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        dehiscence_flag = False
        max_gap_size = 0.0
        gap_boxes: List[List[int]] = []

        if len(contours) > 1:
            # Sort contours by length/area
            sorted_cnts = sorted(contours, key=cv2.contourArea, reverse=True)
            
            # Measure gaps between largest contour segments along main incision axis
            main_cnt = sorted_cnts[0]
            main_rect = cv2.boundingRect(main_cnt)

            for cnt in sorted_cnts[1:5]:
                x, y, w, h = cv2.boundingRect(cnt)
                # Check distance to main contour
                dist = np.min([
                    np.linalg.norm(np.array([x, y]) - np.array([main_rect[0], main_rect[1]])),
                    np.linalg.norm(np.array([x+w, y+h]) - np.array([main_rect[0]+main_rect[2], main_rect[1]+main_rect[3]]))
                ])
                if dist > self.gap_threshold_px and dist < 120:
                    dehiscence_flag = True
                    max_gap_size = max(max_gap_size, float(dist))
                    gap_boxes.append([int(x), int(y), int(w), int(h)])

        # Secondary check: local width expansion of incision site (wound gaping)
        # Check if any horizontal slice across m_wound has a large gap
        y_indices, x_indices = np.where(m_wound > 0)
        if len(y_indices) > 0:
            min_y, max_y = np.min(y_indices), np.max(y_indices)
            widths = []
            for y_slice in range(min_y, max_y, 10):
                row_x = x_indices[y_indices == y_slice]
                if len(row_x) > 0:
                    slice_width = np.max(row_x) - np.min(row_x)
                    widths.append(slice_width)
            
            if len(widths) > 0 and (np.max(widths) - np.median(widths)) > 35:
                dehiscence_flag = True
                max_gap_size = max(max_gap_size, float(np.max(widths) - np.median(widths)))

        return {
            "dehiscence_detected": dehiscence_flag,
            "max_gap_size_px": round(max_gap_size, 2),
            "gap_boxes": gap_boxes,
            "description": "Structural gap / dehiscence along suture line detected." if dehiscence_flag else "Suture line structurally intact."
        }
