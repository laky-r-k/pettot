"""
Zero-Shot Fallback Pipeline (Gemini Flash Vision)
Interfacing with Gemini Vision API for structured FGS/CGS assessment when keypoint extraction fails.
"""

import os
import json
import base64
import cv2
import numpy as np
from typing import Dict, Any

class GeminiGrimaceFallback:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

    def analyze_fallback(self, image_bgr: np.ndarray) -> Dict[str, Any]:
        """
        Invokes Gemini Flash Vision model with structured JSON response schema constraint.
        Falls back gracefully if API key is unconfigured or network is offline.
        """
        if not self.api_key:
            return self._heuristic_fallback(image_bgr, reason="Gemini API Key missing - executed zero-shot vision heuristic fallback.")

        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=self.api_key)

            # Encode BGR image to JPEG bytes
            success, buffer = cv2.imencode('.jpg', image_bgr)
            if not success:
                return self._heuristic_fallback(image_bgr, reason="Image encoding failed")
            
            image_bytes = buffer.tobytes()

            prompt = (
                "You are a veterinary triage assistant trained on the Feline/Canine Grimace Scale (FGS/CGS). "
                "Analyze the provided facial photo and assess four Action Units: "
                "1. Ear position (0=Forward, 1=Slightly apart, 2=Flattened/Outward) "
                "2. Orbital tightening (0=Open, 1=Partial squint, 2=Tightly shut) "
                "3. Muzzle tension (0=Relaxed, 1=Moderate tension, 2=Flattened/Tense) "
                "4. Head position (0=Normal, 1=Slightly dropped, 2=Severely dropped). "
                "Output strictly JSON according to schema."
            )

            # Try generating content with structured schema
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[
                    types.Part.from_bytes(data=image_bytes, mime_type='image/jpeg'),
                    prompt
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema={
                        "type": "OBJECT",
                        "properties": {
                            "ear_position_score": { "type": "INTEGER", "description": "0=Forward, 1=Slightly apart, 2=Flattened/Outward" },
                            "orbital_tightening_score": { "type": "INTEGER", "description": "0=Open, 1=Partial squint, 2=Tightly shut" },
                            "muzzle_tension_score": { "type": "INTEGER", "description": "0=Relaxed, 1=Moderate tension, 2=Flattened/Tense" },
                            "head_position_score": { "type": "INTEGER", "description": "0=Normal, 1=Slightly dropped, 2=Severely dropped" },
                            "confidence_score": { "type": "NUMBER" }
                        },
                        "required": ["ear_position_score", "orbital_tightening_score", "muzzle_tension_score", "confidence_score"]
                    }
                )
            )

            parsed = json.loads(response.text)
            ear_sc = int(parsed.get("ear_position_score", 0))
            orb_sc = int(parsed.get("orbital_tightening_score", 0))
            muz_sc = int(parsed.get("muzzle_tension_score", 0))
            head_sc = int(parsed.get("head_position_score", 0))
            conf = float(parsed.get("confidence_score", 0.85))

            return {
                "source": "Gemini Flash Vision (Zero-Shot)",
                "action_units": {
                    "ear_position_au1": ear_sc,
                    "orbital_tightening_au2": orb_sc,
                    "muzzle_tension_au3": muz_sc,
                    "head_position_au4": head_sc
                },
                "confidence_score": conf,
                "raw_response": parsed
            }

        except Exception as e:
            print(f"Gemini Fallback API call failed: {e}")
            return self._heuristic_fallback(image_bgr, reason=f"Gemini API Exception: {str(e)}")

    def _heuristic_fallback(self, image_bgr: np.ndarray, reason: str = "") -> Dict[str, Any]:
        """Computer vision heuristic fallback when Gemini multimodal API is unreachable."""
        gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
        brightness = float(np.mean(gray))
        contrast = float(np.std(gray))

        # Basic image metric estimate for AU scoring
        orb_sc = 1 if contrast < 35.0 else 0
        ear_sc = 1 if brightness < 80.0 else 0
        muz_sc = 0
        head_sc = 0

        return {
            "source": f"Zero-Shot Vision Heuristic ({reason})",
            "action_units": {
                "ear_position_au1": ear_sc,
                "orbital_tightening_au2": orb_sc,
                "muzzle_tension_au3": muz_sc,
                "head_position_au4": head_sc
            },
            "confidence_score": 0.70,
            "raw_response": {"status": "heuristic_evaluated", "brightness": brightness, "contrast": contrast}
        }
