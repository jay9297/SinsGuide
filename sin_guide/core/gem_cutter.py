from __future__ import annotations

import json
from pathlib import Path

from sin_guide.utils.pob_parser import GemSetup


def load_gem_db(path: Path | None = None) -> dict:
    if path is None:
        path = Path(__file__).parent.parent / "data" / "gems" / "poe2_gems.json"
    with open(path) as f:
        raw = json.load(f)
    db = {}
    for gem_type in ("skill", "spirit", "support"):
        for name, info in raw.get(gem_type, {}).items():
            db[name] = {"type": gem_type, "level": info[0], "attribute": info[1]}
    return db


class GemCutter:
    def __init__(self, gem_db: dict):
        self._db = gem_db

    def get_available_from_vendor(self, ocr_gems: list[str], build_gems: list[GemSetup]) -> list[str]:
        ocr_lower = {g.lower() for g in ocr_gems}
        needed = []
        for gem in build_gems:
            if gem.name.lower() in ocr_lower:
                needed.append(gem.name)
        return needed

    def get_missing_gems(self, ocr_gems: list[str], build_gems: list[GemSetup]) -> list[str]:
        ocr_lower = {g.lower() for g in ocr_gems}
        missing = []
        for gem in build_gems:
            if gem.name.lower() not in ocr_lower:
                missing.append(gem.name)
        return missing

    def get_available_gems(self, player_level: int, build_gems: list[GemSetup]) -> list[dict]:
        results = []
        for gem in build_gems:
            info = self._db.get(gem.name.lower())
            if info is None:
                continue
            req = info["level"]
            if req == 0 or player_level >= req:
                results.append({
                    "name": gem.name,
                    "type": info["type"],
                    "level_required": req,
                    "unknown": req == 0,
                })
        return results

    def get_upcoming_gems(self, player_level: int, build_gems: list[GemSetup], horizon: int = 3) -> list[dict]:
        results = []
        for gem in build_gems:
            info = self._db.get(gem.name.lower())
            if info is None:
                continue
            req = info["level"]
            if req > player_level and req <= player_level + horizon:
                results.append({
                    "name": gem.name,
                    "type": info["type"],
                    "level_required": req,
                    "levels_away": req - player_level,
                })
        return results

    def get_gems_needing_level_up(self, player_level: int, build_gems: list[GemSetup]) -> list[dict]:
        """Return gems where the character level required to use the gem
        is more than one level above the player's current level."""
        results = []
        for gem in build_gems:
            info = self._db.get(gem.name.lower())
            if info is None:
                continue
            req = info["level"]
            if req > player_level + 1:
                results.append({
                    "name": gem.name,
                    "type": info["type"],
                    "level_required": req,
                    "player_level": player_level,
                })
        return results
