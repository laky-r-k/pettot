"""
Infection & Erythema Detection via HSV Segmentation
Implements Sobel Incision Line Isolation (M_wound with 15px buffer), Dual Red-Hue HSV Masking, Morphological Cleanup, and Er calculation.
"""

import cv2
import numpy as np
from typing import Dict, Any, Tuple

class ErythemaSegmenter:
    def __init__(self, buffer_radius: int = 15, sat_min: int = 50, val_min: int = 40):
        self.buffer_radius = buffer_radius
        self.sat_min = sat_min
        self.val_min = val_min

    def isolate_incision_mask(self, image_bgr: np.ndarray) -> np.ndarray:
        """
        Applies Sobel gradient filtering to identify suture lines / wound margins.
        Creates a dilated binary mask (M_wound) representing primary incision site plus 15px radius buffer.
        """
        gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # Sobel edge detection along X and Y
        sobel_x = cv2.Sobel(blurred, cv2.CV_64F, 1, 0, ksize=3)
        sobel_y = cv2.Sobel(blurred, cv2.CV_64F, 0, 1, ksize=3)
        sobel_mag = np.sqrt(sobel_x**2 + sobel_y**2)

        # Normalize to 0-255 uint8
        sobel_norm = cv2.normalize(sobel_mag, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)

        # Threshold top edge pixels to isolate suture line / wound margin
        _, binary_edges = cv2.threshold(sobel_norm, 40, 255, cv2.THRESH_BINARY)

        # Dilate mask with 15-pixel radius surrounding buffer
        kernel_size = self.buffer_radius * 2 + 1
        dilation_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
        m_wound = cv2.dilate(binary_edges, dilation_kernel, iterations=1)

        return m_wound

    def segment_erythema_hsv(self, image_bgr: np.ndarray) -> np.ndarray:
        """
        Segment red/pink hue spectrums associated with inflammation in HSV space:
        Hue Range 1: 0 deg <= H <= 12 deg (Deep Reds / Active Inflammation)
        Hue Range 2: 165 deg <= H <= 180 deg (Magenta-Reds)
        Saturation Filter: S >= 50 (filters out normal skin tones)
        Value Filter: V >= 40
        """
        hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)

        # OpenCV H ranges from 0 to 180 (degrees / 2)
        # 0..12 degrees -> H in [0, 6] or [0, 12]
        # 165..180 degrees -> H in [82, 90] or [165, 180]
        lower_red1 = np.array([0, self.sat_min, self.val_min])
        upper_red1 = np.array([12, 255, 255])

        lower_red2 = np.array([165, self.sat_min, self.val_min])
        upper_red2 = np.array([180, 255, 255])

        mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
        mask2 = cv2.inRange(hsv, lower_red2, upper_red2)

        # Dual Red-Hue Masking
        erythema_mask = cv2.bitwise_or(mask1, mask2)

        # Morphological Cleanup (Opening to remove noise, Closing to fill small holes)
        morph_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        cleaned_mask = cv2.morphologyEx(erythema_mask, cv2.MORPH_OPEN, morph_kernel)
        cleaned_mask = cv2.morphologyEx(cleaned_mask, cv2.MORPH_CLOSE, morph_kernel)

        return cleaned_mask

    def calculate_erythema_pixel_ratio(self, image_bgr: np.ndarray) -> Dict[str, Any]:
        """
        Calculates Erythema Pixel Ratio (E_r):
        E_r = ( sum(P_red INTERSECT M_wound) / sum(P_total INTERSECT M_wound) ) * 100
        """
        m_wound = self.isolate_incision_mask(image_bgr)
        erythema_mask = self.segment_erythema_hsv(image_bgr)

        # Intersection of Red pixels and Wound Mask M_wound
        red_in_wound = cv2.bitwise_and(erythema_mask, erythema_mask, mask=m_wound)

        total_wound_pixels = np.count_nonzero(m_wound)
        red_wound_pixels = np.count_nonzero(red_in_wound)

        if total_wound_pixels == 0:
            e_r = 0.0
        else:
            e_r = (red_wound_pixels / float(total_wound_pixels)) * 100.0

        return {
            "erythema_ratio_er": float(e_r),
            "total_wound_pixels": int(total_wound_pixels),
            "red_wound_pixels": int(red_wound_pixels),
            "m_wound": m_wound,
            "erythema_mask": erythema_mask,
            "red_in_wound_mask": red_in_wound
        }
