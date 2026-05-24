"""Tests for gem OCR — synthetic image OCR extraction."""
from __future__ import annotations

import pytest
from PIL import Image, ImageDraw, ImageFont

from sin_guide.core.gem_ocr import GemOCR, preprocess_screenshot


@pytest.fixture()
def gem_ui_image():
    w, h = 800, 400
    img = Image.new("RGB", (w, h), color=(20, 20, 20))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/usr/share/fonts/dejavu/DejaVuSans.ttf", 22)
    except OSError:
        font = ImageFont.load_default()
    x = int(w * 0.70) + 20
    y = int(h * 0.30) + 20
    for name in ["Fireball", "Frostbolt", "Herald of Ice", "Spark"]:
        draw.text((x, y), name, fill=(255, 255, 255), font=font)
        y += 40
    return img


@pytest.fixture()
def full_screenshot():
    w, h = 960, 540
    img = Image.new("RGB", (w, h), color=(10, 10, 10))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/usr/share/fonts/dejavu/DejaVuSans.ttf", 18)
    except OSError:
        font = ImageFont.load_default()

    draw.text((10, 10), "HUD: 100%", fill=(200, 200, 200), font=font)
    draw.text((10, 40), "Zone: The Coast", fill=(200, 200, 200), font=font)

    roi_left = int(w * 0.70)
    roi_top = int(h * 0.30)
    x = roi_left + 20
    y = roi_top + 20
    for name in ["Fireball", "Frostbolt", "Herald of Ice", "Spark"]:
        draw.text((x, y), name, fill=(255, 255, 255), font=font)
        y += 35

    return img


class TestPreprocessScreenshot:
    def test_crops_to_roi(self, full_screenshot):
        w, h = full_screenshot.size
        processed = preprocess_screenshot(full_screenshot)
        expected_w = int(w * 0.30) * 2
        expected_h = int(h * 0.40) * 2
        pw, ph = processed.size
        assert pw == expected_w, f"Expected width {expected_w}, got {pw}"
        assert ph == expected_h, f"Expected height {expected_h}, got {ph}"

    def test_output_is_grayscale(self, full_screenshot):
        processed = preprocess_screenshot(full_screenshot)
        assert processed.mode == "L"

    def test_scales_up_2x(self, full_screenshot):
        w, h = full_screenshot.size
        roi_w = int(w * 0.30)
        roi_h = int(h * 0.40)
        processed = preprocess_screenshot(full_screenshot)
        pw, ph = processed.size
        assert pw == roi_w * 2
        assert ph == roi_h * 2

    def test_extracts_gem_names_through_preprocessing(self, full_screenshot):
        ocr = GemOCR()
        names = ocr.extract_names_from_image(full_screenshot)
        lower = [n.lower() for n in names]
        assert "fireball" in lower
        assert "frostbolt" in lower
        assert "herald of ice" in lower


class TestMatchGemName:
    """Fuzzy gem name matching against the database."""

    def test_exact_match_returns_db_key(self):
        from sin_guide.core.gem_ocr import match_gem_name

        db = {"fireball": {}, "frostbolt": {}, "spark": {}}
        assert match_gem_name("fireball", db) == "fireball"

    def test_case_insensitive_matching(self):
        from sin_guide.core.gem_ocr import match_gem_name

        db = {"fireball": {}}
        assert match_gem_name("Fireball", db) == "fireball"
        assert match_gem_name("FIREBALL", db) == "fireball"
        assert match_gem_name("  Fireball  ", db) == "fireball"

    def test_typo_fuzzy_match(self):
        from sin_guide.core.gem_ocr import match_gem_name

        db = {"fireball": {}, "frostbolt": {}, "herald of ice": {}}
        assert match_gem_name("Firebal", db) == "fireball"
        assert match_gem_name("Frostblot", db) == "frostbolt"
        assert match_gem_name("Herald of Ice", db) == "herald of ice"

    def test_garbage_input_returns_none(self):
        from sin_guide.core.gem_ocr import match_gem_name

        db = {"fireball": {}, "spark": {}}
        assert match_gem_name("xyqwrtyw", db) is None
        assert match_gem_name("zzzzzz", db) is None

    def test_below_threshold_returns_none(self):
        from sin_guide.core.gem_ocr import match_gem_name

        db = {"fireball": {}}
        assert match_gem_name("warlock", db, threshold=90) is None

    def test_short_input_rejected(self):
        from sin_guide.core.gem_ocr import match_gem_name

        db = {"arc": {}}
        assert match_gem_name("a", db) is None
        assert match_gem_name("ar", db) == "arc"


class TestGemOCRWithDatabase:
    """OCR extraction with gem database validation."""

    def test_extracts_only_valid_gem_names(self, gem_ui_image):
        from sin_guide.core.gem_ocr import GemOCR

        db = {
            "fireball": {},
            "frostbolt": {},
            "herald of ice": {},
            "spark": {},
        }
        ocr = GemOCR()
        names = ocr.extract_names_from_image(gem_ui_image, gem_db=db)
        for name in names:
            assert name in db, f"{name!r} not in gem database"
        assert len(names) >= 1, "Should find at least one valid gem"

    def test_no_gem_db_returns_all_cleaned_names(self, gem_ui_image):
        from sin_guide.core.gem_ocr import GemOCR

        ocr = GemOCR()
        names = ocr.extract_names_from_image(gem_ui_image)
        lower = {n.lower() for n in names}
        assert "fireball" in lower
        assert "frostbolt" in lower

    def test_empty_db_filters_everything(self, gem_ui_image):
        from sin_guide.core.gem_ocr import GemOCR

        ocr = GemOCR()
        names = ocr.extract_names_from_image(gem_ui_image, gem_db={})
        assert names == []


class TestGemOCR:
    def test_extracts_gem_names_from_image(self, gem_ui_image):
        from sin_guide.core.gem_ocr import GemOCR
        ocr = GemOCR()
        names = ocr.extract_names_from_image(gem_ui_image)
        lower = [n.lower() for n in names]
        assert "fireball" in lower
        assert "frostbolt" in lower
        assert "herald of ice" in lower

    def test_get_build_recommendations(self, gem_ui_image):
        from sin_guide.core.gem_ocr import GemOCR
        from sin_guide.core.gem_cutter import GemCutter
        from sin_guide.utils.pob_parser import GemSetup

        db = {
            "fireball": {"type": "skill", "level": 3, "attribute": 3},
            "frostbolt": {"type": "skill", "level": 5, "attribute": 3},
            "herald of ice": {"type": "spirit", "level": 4, "attribute": 3},
            "spark": {"type": "skill", "level": 4, "attribute": 3},
        }
        build = [
            GemSetup("Fireball", 1, []),
            GemSetup("Herald of Ice", 1, []),
            GemSetup("Ice Nova", 1, []),
        ]

        ocr = GemOCR()
        cutter = GemCutter(db)
        ocr_names = ocr.extract_names_from_image(gem_ui_image)
        needed = cutter.get_available_from_vendor(ocr_names, build)

        assert "Fireball" in needed
        assert "Herald of Ice" in needed
        assert "Ice Nova" not in needed
