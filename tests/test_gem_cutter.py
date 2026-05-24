"""Tests for GemCutter — gem availability and build intersection logic."""
from __future__ import annotations

import pytest

from sin_guide.utils.pob_parser import GemSetup


GEM_DB = {
    "fireball": {"type": "skill", "level": 3, "attribute": 3},
    "frostbolt": {"type": "skill", "level": 5, "attribute": 3},
    "spark": {"type": "skill", "level": 4, "attribute": 3},
    "ice nova": {"type": "skill", "level": 6, "attribute": 3},
    "herald of ice": {"type": "spirit", "level": 4, "attribute": 3},
    "brutality i": {"type": "support", "level": 1, "attribute": 1},
}


class TestGetAvailableFromVendor:
    def test_intersects_ocr_with_build_gems(self):
        from sin_guide.core.gem_cutter import GemCutter
        cutter = GemCutter(GEM_DB)
        ocr_gems = ["fireball", "frostbolt", "spark"]
        build_gems = [
            GemSetup("fireball", 1, []),
            GemSetup("ice nova", 1, []),
        ]
        needed = cutter.get_available_from_vendor(ocr_gems, build_gems)
        assert "fireball" in needed
        assert "ice nova" not in needed

    def test_empty_when_no_overlap(self):
        from sin_guide.core.gem_cutter import GemCutter
        cutter = GemCutter(GEM_DB)
        ocr_gems = ["spark", "frostbolt"]
        build_gems = [GemSetup("fireball", 1, []), GemSetup("ice nova", 1, [])]
        needed = cutter.get_available_from_vendor(ocr_gems, build_gems)
        assert needed == []


class TestGetAvailableGems:
    def test_returns_gems_at_or_below_player_level(self):
        from sin_guide.core.gem_cutter import GemCutter
        cutter = GemCutter(GEM_DB)
        build_gems = [
            GemSetup("fireball", 1, []),
            GemSetup("spark", 1, []),
            GemSetup("ice nova", 1, []),
        ]
        available = cutter.get_available_gems(player_level=4, build_gems=build_gems)
        names = [g["name"] for g in available]
        assert "fireball" in names
        assert "spark" in names
        assert "ice nova" not in names

    def test_returns_upcoming_gems_within_horizon(self):
        from sin_guide.core.gem_cutter import GemCutter
        cutter = GemCutter(GEM_DB)
        build_gems = [
            GemSetup("fireball", 1, []),
            GemSetup("ice nova", 1, []),
        ]
        upcoming = cutter.get_upcoming_gems(player_level=3, build_gems=build_gems, horizon=3)
        names = [g["name"] for g in upcoming]
        assert "ice nova" in names
        assert "fireball" not in names


class TestGetMissingGems:
    def test_returns_build_gems_not_in_ocr(self):
        from sin_guide.core.gem_cutter import GemCutter
        cutter = GemCutter(GEM_DB)
        ocr_gems = ["fireball", "spark"]
        build_gems = [
            GemSetup("fireball", 1, []),
            GemSetup("ice nova", 1, []),
        ]
        missing = cutter.get_missing_gems(ocr_gems, build_gems)
        assert "ice nova" in missing
        assert "fireball" not in missing

    def test_returns_all_when_no_ocr_match(self):
        from sin_guide.core.gem_cutter import GemCutter
        cutter = GemCutter(GEM_DB)
        ocr_gems = ["spark", "frostbolt"]
        build_gems = [GemSetup("fireball", 1, []), GemSetup("ice nova", 1, [])]
        missing = cutter.get_missing_gems(ocr_gems, build_gems)
        assert "fireball" in missing
        assert "ice nova" in missing

    def test_returns_empty_when_all_match(self):
        from sin_guide.core.gem_cutter import GemCutter
        cutter = GemCutter(GEM_DB)
        ocr_gems = ["fireball", "ice nova"]
        build_gems = [
            GemSetup("fireball", 1, []),
            GemSetup("ice nova", 1, []),
        ]
        missing = cutter.get_missing_gems(ocr_gems, build_gems)
        assert missing == []
