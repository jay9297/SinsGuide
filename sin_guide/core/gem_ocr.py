from __future__ import annotations

import difflib
import re

import pytesseract
from PIL import Image


def preprocess_screenshot(image: Image.Image) -> Image.Image:
    """Crop, threshold, and scale a screenshot for OCR on the gem panel.

    Pipeline:
      1. Crop to right-center 30% width, middle 40% height (gem panel ROI).
      2. Convert to grayscale.
      3. Apply binary threshold (~128) to increase contrast.
      4. Scale up 2x for better tesseract accuracy.
    """
    w, h = image.size

    # Crop to gem panel ROI: right-center 30% width, middle 40% height.
    left = int(w * 0.70)
    right = w
    top = int(h * 0.30)
    bottom = int(h * 0.70)
    cropped = image.crop((left, top, right, bottom))
    gray = cropped.convert("L")
    binary = gray.point(lambda x: 255 if x > 128 else 0)
    bw, bh = binary.size
    scaled = binary.resize((bw * 2, bh * 2), Image.LANCZOS)

    return scaled


def match_gem_name(ocr_name: str, gem_db: dict, threshold: int = 80) -> str | None:
    """Fuzzy match an OCR-extracted name against the gem database.

    Uses difflib.get_close_matches for case-insensitive similarity matching.
    Only returns a result when the similarity ratio meets the threshold.

    Args:
        ocr_name: Raw name from OCR (case-insensitive matching).
        gem_db: Gem database dict where keys are lowercase gem names.
        threshold: Similarity threshold as a percentage (0-100). Default is 80,
                   meaning the SequenceMatcher ratio must be ≥ 0.80.

    Returns:
        The matched gem name (database key) or None if no match meets the threshold.
    """
    ocr_lower = ocr_name.lower().strip()
    matches = difflib.get_close_matches(
        ocr_lower, gem_db.keys(), n=1, cutoff=threshold / 100.0
    )
    return matches[0] if matches else None


class GemOCR:
    def extract_names_from_image(
        self, image: Image.Image, gem_db: dict | None = None, preprocess: bool = True
    ) -> list[str]:
        proc_img = preprocess_screenshot(image) if preprocess else image
        text = pytesseract.image_to_string(proc_img)
        names = []
        for line in text.splitlines():
            clean = self._clean_gem_name(line.strip())
            if not clean:
                continue
            if gem_db is not None:
                matched = match_gem_name(clean, gem_db)
                if matched:
                    names.append(matched)
            else:
                names.append(clean)
        return names

    @staticmethod
    def _clean_gem_name(raw: str) -> str:
        raw = re.sub(r"[^a-zA-Z\s']", "", raw).strip()
        if len(raw) < 3:
            return ""
        if raw.lower() in ("uncut", "skill gem", "spirit gem", "support gem"):
            return ""
        return raw
