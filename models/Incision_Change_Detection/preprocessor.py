"""
Pre-Processing & Alignment Pipeline
Handles bounding box cropping with 20% border, Gray-World color normalization, and 512x512 spatial scale normalization.
"""

import cv2
import numpy as np
from typing import Tuple, Optional, Dict, Any

class ImagePreprocessor:
    def __init__(self, target_size: Tuple[int, int] = (512, 512), border_expansion: float = 0.20):
        self.target_size = target_size
        self.border_expansion = border_expansion

    def crop_surgical_region(self, image: np.ndarray, bbox: Optional[Tuple[int, int, int, int]] = None) -> np.ndarray:
        """
        Crops surgical region given bounding box (x, y, w, h) with 20% outer border expansion.
        If bbox is None, uses center 80% region.
        """
        h, w, _ = image.shape

        if bbox is None:
            # Default center crop with padding
            bx, by, bw, bh = int(w * 0.15), int(h * 0.15), int(w * 0.70), int(h * 0.70)
        else:
            bx, by, bw, bh = bbox

        # Expand bounding box by border_expansion (20%)
        pad_w = int(bw * self.border_expansion)
        pad_h = int(bh * self.border_expansion)

        x1 = max(0, bx - pad_w)
        y1 = max(0, by - pad_h)
        x2 = min(w, bx + bw + pad_w)
        y2 = min(h, by + bh + pad_h)

        cropped = image[y1:y2, x1:x2]
        return cropped

    def gray_world_normalization(self, image: np.ndarray) -> np.ndarray:
        """
        Applies Gray-World Color Normalization to eliminate home lighting color casts
        (e.g., warm incandescent vs cool daylight).
        Scales color channels (B, G, R) so mean(B) = mean(G) = mean(R) = gray_mean.
        """
        image_float = image.astype(np.float32)
        
        b_mean = np.mean(image_float[:, :, 0]) + 1e-6
        g_mean = np.mean(image_float[:, :, 1]) + 1e-6
        r_mean = np.mean(image_float[:, :, 2]) + 1e-6

        gray_mean = (b_mean + g_mean + r_mean) / 3.0

        image_float[:, :, 0] = np.clip(image_float[:, :, 0] * (gray_mean / b_mean), 0, 255)
        image_float[:, :, 1] = np.clip(image_float[:, :, 1] * (gray_mean / g_mean), 0, 255)
        image_float[:, :, 2] = np.clip(image_float[:, :, 2] * (gray_mean / r_mean), 0, 255)

        return image_float.astype(np.uint8)

    def spatial_scale_normalization(self, image: np.ndarray) -> np.ndarray:
        """Resizes image to standard 512x512px resolution."""
        return cv2.resize(image, self.target_size, interpolation=cv2.INTER_AREA)

    def process(self, image: np.ndarray, bbox: Optional[Tuple[int, int, int, int]] = None) -> np.ndarray:
        """
        Executes complete pre-processing pipeline:
        Bounding Box Crop (20% border) -> Gray-World Normalization -> Spatial Scale Normalization (512x512).
        """
        cropped = self.crop_surgical_region(image, bbox)
        normalized_color = self.gray_world_normalization(cropped)
        scaled_image = self.spatial_scale_normalization(normalized_color)
        return scaled_image
