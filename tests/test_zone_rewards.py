"""Tests for zone league mechanic rewards."""
from __future__ import annotations

import json
from pathlib import Path

from sin_guide.data.zone_rewards import ZONE_LEAGUE_REWARDS, ZONES_WITHOUT_REWARDS


CAMPAIGN_PATH = Path(__file__).parent.parent / "sin_guide" / "data" / "guides" / "poe2_campaign.json"


def _load_campaign_zones() -> set[str]:
    with open(CAMPAIGN_PATH) as f:
        data = json.load(f)
    return {step["zone"] for step in data["steps"]}


class TestZoneRewardData:
    def test_all_campaign_zones_have_rewards_or_are_excluded(self):
        campaign_zones = _load_campaign_zones()
        rewarded_zones = set(ZONE_LEAGUE_REWARDS.keys())
        excluded_zones = ZONES_WITHOUT_REWARDS
        covered = rewarded_zones | excluded_zones
        missing = campaign_zones - covered
        assert not missing, f"Campaign zones with no reward and not excluded: {missing}"

    def test_no_extra_zones_in_rewards(self):
        campaign_zones = _load_campaign_zones()
        extra = set(ZONE_LEAGUE_REWARDS.keys()) - campaign_zones
        assert not extra, f"Reward entries for zones not in campaign: {extra}"

    def test_no_excluded_zones_in_rewards(self):
        overlap = set(ZONE_LEAGUE_REWARDS.keys()) & ZONES_WITHOUT_REWARDS
        assert not overlap, f"Zones in both rewards and excluded: {overlap}"

    def test_all_rewards_within_char_limit(self):
        for zone, reward in ZONE_LEAGUE_REWARDS.items():
            full_text = f"League: {reward}"
            assert len(full_text) <= 30, (
                f"{zone}: '{full_text}' is {len(full_text)} chars (max 30)"
            )

    def test_no_empty_rewards(self):
        for zone, reward in ZONE_LEAGUE_REWARDS.items():
            assert reward, f"{zone} has empty reward"


class TestZoneRewardLookup:
    def test_mud_burrow_reward(self):
        from sin_guide.data.zone_rewards import ZONE_LEAGUE_REWARDS
        assert ZONE_LEAGUE_REWARDS.get("The Mud Burrow", "") == "Orb of Augmentation"

    def test_unknown_zone_returns_empty(self):
        from sin_guide.data.zone_rewards import ZONE_LEAGUE_REWARDS
        assert ZONE_LEAGUE_REWARDS.get("Nonexistent Zone", "") == ""

    def test_clearfell_reward(self):
        from sin_guide.data.zone_rewards import ZONE_LEAGUE_REWARDS
        assert ZONE_LEAGUE_REWARDS.get("Clearfell", "") == "Orb of Transmutation"


class TestStepRendererRewards:
    def test_reward_label_rendered_for_known_zone(self, qtbot):
        from PySide6.QtWidgets import QVBoxLayout
        from sin_guide.overlay.step_renderer import render_steps
        from sin_guide.core.guide_engine import GuideStep

        container = QVBoxLayout()
        steps = [
            GuideStep(
                id="s1", act=1, zone="Clearfell", step_number=1,
                description="Loot stash", step_type="loot", target="",
                hint="", tags=["mandatory"], next_steps=[],
                auto_advance_trigger=None,
            )
        ]
        render_steps(container, steps, 300, ZONE_LEAGUE_REWARDS)

        labels = []
        for i in range(container.count()):
            widget = container.itemAt(i).widget()
            if widget is not None:
                labels.append(widget.text())

        assert "League: Orb of Transmutation" in labels

    def test_no_reward_label_when_zone_excluded(self, qtbot):
        from PySide6.QtWidgets import QVBoxLayout
        from sin_guide.overlay.step_renderer import render_steps
        from sin_guide.core.guide_engine import GuideStep

        container = QVBoxLayout()
        steps = [
            GuideStep(
                id="s1", act=1, zone="The Riverbank", step_number=1,
                description="Tutorial", step_type="generic", target="",
                hint="", tags=["mandatory"], next_steps=[],
                auto_advance_trigger=None,
            )
        ]
        render_steps(container, steps, 300, ZONE_LEAGUE_REWARDS)

        labels = []
        for i in range(container.count()):
            widget = container.itemAt(i).widget()
            if widget is not None:
                labels.append(widget.text())

        assert "League: The Riverbank" not in labels

    def test_no_reward_labels_when_zone_rewards_none(self, qtbot):
        from PySide6.QtWidgets import QVBoxLayout
        from sin_guide.overlay.step_renderer import render_steps
        from sin_guide.core.guide_engine import GuideStep

        container = QVBoxLayout()
        steps = [
            GuideStep(
                id="s1", act=1, zone="Clearfell", step_number=1,
                description="Loot stash", step_type="loot", target="",
                hint="", tags=["mandatory"], next_steps=[],
                auto_advance_trigger=None,
            )
        ]
        render_steps(container, steps, 300, None)

        labels = []
        for i in range(container.count()):
            widget = container.itemAt(i).widget()
            if widget is not None:
                labels.append(widget.text())

        assert not any(label.startswith("League:") for label in labels)

    def test_none_string_reward_filtered_out(self, qtbot):
        from PySide6.QtWidgets import QVBoxLayout
        from sin_guide.overlay.step_renderer import render_steps
        from sin_guide.core.guide_engine import GuideStep

        container = QVBoxLayout()
        steps = [
            GuideStep(
                id="s1", act=1, zone="TestZone", step_number=1,
                description="Test step", step_type="generic", target="",
                hint="", tags=["mandatory"], next_steps=[],
                auto_advance_trigger=None,
            )
        ]
        render_steps(container, steps, 300, {"TestZone": "None"})

        labels = []
        for i in range(container.count()):
            widget = container.itemAt(i).widget()
            if widget is not None:
                labels.append(widget.text())

        assert not any(label.startswith("League:") for label in labels)
