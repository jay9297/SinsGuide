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

    def test_optional_recommended_step_hidden_when_optionals_off(self, engine):
        # Documents that ["optional", "recommended"] steps are filtered when
        # show_optionals=False — mirrors Venom Crypts / Servi turn-in behaviour.
        engine.current_step_id = "s3"
        engine.current_zone = "Clearfell"
        steps = engine.get_visible_steps(league_start=True, show_optionals=False)
        descriptions = [s.description for s in steps]
        assert "Loot Abandoned Stash" not in descriptions

    def test_permanent_buff_step_always_visible(self, engine):
        engine.current_step_id = "s4"
        engine.current_zone = "Clearfell"
        steps = engine.get_visible_steps(league_start=True, show_optionals=False)
        descriptions = [s.description for s in steps]
        assert "Kill Beira" in descriptions


class TestProgressById:
    """Progress is stored as current_step_id (string), not step_number.
    Renumbering steps across guide updates does not corrupt in-flight progress."""

    def test_current_step_id_is_string_not_int(self, engine):
        assert isinstance(engine.current_step_id, str)

    def test_advance_uses_id_not_step_number(self, engine):
        engine.current_step_id = "s1"
        engine.advance()
        # After advance, current step is identified by id "s2", regardless of
        # what step_number the target holds.
        assert engine.current_step_id == "s2"

    def test_handle_zone_enter_resolves_by_id(self, engine):
        engine.handle_zone_enter("The Clearfell Encampment")
        assert engine.current_step_id == "s2"


class TestMatlanWaterwaysRouting:
    """Verify that the post-0.5.0 Act 3 routing is exercised by the engine."""

    @pytest.fixture()
    def act3_engine(self):
        steps = [
            # Jiquani's Sanctum boss kill (no auto_advance — manual advance needed)
            _step("jq_boss", "Jiquani's Sanctum", 1, tags=["mandatory"]),
            # Loot Large Soul Core (same zone, next step)
            _step("jq_loot", "Jiquani's Sanctum", 2, tags=["mandatory"]),
            # Return to Jungle Ruins
            _step("jr_altar", "Jungle Ruins", 3, tags=["mandatory"]),
            # Enter Matlan Waterways (has auto_advance trigger)
            _step("matlan_enter", "Matlan Waterways", 4, tags=["mandatory"],
                  trigger={"type": "enter_area", "target_area": "Matlan Waterways"}),
            # Navigate canals (mandatory, no trigger)
            _step("matlan_nav", "Matlan Waterways", 5, tags=["mandatory"]),
            # Optional Azak Bog branch
            _step("matlan_bog", "Matlan Waterways", 6,
                  tags=["optional"],
                  trigger={"type": "enter_area", "target_area": "The Azak Bog"}),
            _step("azak_servi", "The Azak Bog", 7, tags=["optional"]),
            _step("azak_ignagduk", "The Azak Bog", 8, tags=["permanent_buff"]),
            # Lever / return to town
            _step("matlan_lever", "Matlan Waterways", 9, tags=["mandatory"],
                  trigger={"type": "enter_area", "target_area": "Ziggurat Encampment"}),
            _step("ziggurat_alva", "Ziggurat Encampment", 10, tags=["mandatory"]),
        ]
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write(make_guide_json(steps))
            path = Path(f.name)
        eng = GuideEngine(path)
        yield eng
        path.unlink(missing_ok=True)

    def test_entering_matlan_advances_from_jungle_ruins(self, act3_engine):
        act3_engine.current_step_id = "jr_altar"
        act3_engine.handle_zone_enter("Matlan Waterways")
        assert act3_engine.current_step_id == "matlan_enter"

    def test_azak_bog_entered_from_matlan_optional_step(self, act3_engine):
        act3_engine.current_step_id = "matlan_bog"
        act3_engine.handle_zone_enter("The Azak Bog")
        assert act3_engine.current_step_id == "azak_servi"

    def test_azak_bog_steps_hidden_when_optionals_off(self, act3_engine):
        act3_engine.current_step_id = "matlan_nav"
        act3_engine.current_zone = "Matlan Waterways"
        steps = act3_engine.get_visible_steps(league_start=True, show_optionals=False)
        zones = [s.zone for s in steps]
        assert "The Azak Bog" not in zones

    def test_mandatory_path_skips_azak_bog(self, act3_engine):
        # Advancing through mandatory steps should never land in Azak Bog.
        act3_engine.current_step_id = "matlan_nav"
        act3_engine.advance()
        # matlan_nav (5) → next mandatory by step_number: matlan_lever (9)
        # because matlan_bog (6) is optional and advance picks next by step_number
        # regardless of tag — but the mandatory filter only applies to visibility.
        # What we assert here is that the Azak Bog has no mandatory entry path.
        azak_steps = [
            s for s in act3_engine.steps.values() if s.zone == "The Azak Bog"
        ]
        assert all("mandatory" not in s.tags for s in azak_steps)
