"""Behavioral tests for GuideEngine — advance, retreat, zone enter, visible steps."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from sin_guide.core.guide_engine import GuideEngine


def make_guide_json(steps: list[dict]) -> str:
    return json.dumps({"version": "1.0", "game": "poe2", "acts": [1, 2], "steps": steps})


def _step(id, zone, step_number, description="Test", tags=None, trigger=None):
    return {
        "id": id, "act": 1, "zone": zone, "step_number": step_number,
        "description": description, "type": "generic", "target": "", "hint": "",
        "tags": tags or ["mandatory"], "next_steps": [],
        "auto_advance_trigger": trigger,
    }


@pytest.fixture()
def engine():
    steps = [
        _step("s1", "The Riverbank", 1, description="Kill Bloated Miller",
              trigger={"type": "enter_area", "target_area": "The Clearfell Encampment"}),
        _step("s2", "The Clearfell Encampment", 2, description="Talk to Renly"),
        _step("s3", "Clearfell", 3, description="Loot Abandoned Stash", tags=["optional"]),
        _step("s4", "Clearfell", 4, description="Kill Beira", tags=["permanent_buff"],
              trigger={"type": "enter_area", "target_area": "The Mud Burrow"}),
        _step("s5", "The Mud Burrow", 5, description="Kill Devourer"),
    ]
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write(make_guide_json(steps))
        path = Path(f.name)
    engine = GuideEngine(path)
    yield engine
    path.unlink(missing_ok=True)


class TestAdvanceRetreat:
    def test_advance_moves_to_next_step(self, engine):
        assert engine.current_step_id == "s1"
        engine.advance()
        assert engine.current_step_id == "s2"

    def test_advance_skips_past_steps(self, engine):
        engine.current_step_id = "s2"
        engine.advance()
        assert engine.current_step_id == "s3"

    def test_retreat_moves_to_previous(self, engine):
        engine.current_step_id = "s3"
        engine.retreat()
        assert engine.current_step_id == "s2"

    def test_retreat_from_first_step_does_nothing(self, engine):
        engine.retreat()
        assert engine.current_step_id == "s1"

    def test_advance_past_last_step_does_nothing(self, engine):
        engine.current_step_id = "s5"
        engine.advance()
        assert engine.current_step_id == "s5"


class TestZoneEnter:
    def test_trigger_on_current_step_advances(self, engine):
        engine.handle_zone_enter("The Clearfell Encampment")
        assert engine.current_step_id == "s2"

    def test_zone_without_trigger_uses_fallback(self, engine):
        engine.current_step_id = "s2"
        engine.handle_zone_enter("Clearfell")
        assert engine.current_step_id == "s3"

    def test_zone_enter_sets_current_zone(self, engine):
        engine.handle_zone_enter("Clearfell")
        assert engine.current_zone == "Clearfell"


class TestVisibleSteps:
    def test_visible_steps_match_current_zone(self, engine):
        engine.current_step_id = "s3"
        engine.current_zone = "Clearfell"
        steps = engine.get_visible_steps(league_start=True, show_optionals=True)
        descriptions = [s.description for s in steps]
        assert "Loot Abandoned Stash" in descriptions
        assert "Kill Beira" in descriptions

    def test_visible_steps_exclude_optionals_when_disabled(self, engine):
        engine.current_step_id = "s3"
        engine.current_zone = "Clearfell"
        steps = engine.get_visible_steps(league_start=True, show_optionals=False)
        descriptions = [s.description for s in steps]
        assert "Loot Abandoned Stash" not in descriptions

    def test_empty_when_no_current_step(self, engine):
        engine.current_step_id = None
        assert engine.get_visible_steps(True, True) == []
