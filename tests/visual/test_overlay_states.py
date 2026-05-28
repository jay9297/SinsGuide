# tests/visual/test_overlay_states.py
"""Visual regression tests for OverlayWindow.

Run normally:
    pytest tests/visual/ -v

Regenerate all baselines (first run, or after intentional UI changes):
    pytest tests/visual/ --update-snapshots -v
"""
from __future__ import annotations


from tests.conftest import make_step


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _grab(overlay):
    """Grab the main_frame only (excludes the transparent outer widget)."""
    return overlay.main_frame.grab()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestSingleStep:
    def test_act1_mandatory_step(self, make_overlay, assert_matches_snapshot):
        """Single mandatory step; timer visible; exp hidden."""
        steps = [make_step(
            id="s1", act=1, zone="The Riverbank", step_number=1,
            description="Kill Renly and loot the Waypoint.",
        )]
        overlay = make_overlay(steps=steps, timer_display="0:32 | A1 | 0:32")
        assert_matches_snapshot(_grab(overlay), "act1_mandatory_step")

    def test_act3_step(self, make_overlay, assert_matches_snapshot):
        """Confirms act header updates correctly in later acts."""
        steps = [make_step(
            id="s1", act=3, zone="Ogham Village", step_number=42,
            description="Enter the Manor Ramparts.",
        )]
        overlay = make_overlay(steps=steps, timer_display="1:14 | A3 | 0:12")
        assert_matches_snapshot(_grab(overlay), "act3_step")


class TestStepStyling:
    def test_optional_step(self, make_overlay, assert_matches_snapshot):
        """Optional steps render in grey (#cccccc)."""
        steps = [make_step(
            id="s1", act=1, zone="The Riverbank", step_number=1,
            description="Optional: collect the Flask.",
            tags=["optional"],
        )]
        overlay = make_overlay(steps=steps)
        assert_matches_snapshot(_grab(overlay), "optional_step")

    def test_permanent_buff_step(self, make_overlay, assert_matches_snapshot):
        """Permanent buff steps render in cyan (#00ffff)."""
        steps = [make_step(
            id="s1", act=1, zone="The Riverbank", step_number=1,
            description="Pick up Stamina Charm.",
            tags=["permanent_buff"],
        )]
        overlay = make_overlay(steps=steps)
        assert_matches_snapshot(_grab(overlay), "permanent_buff_step")

    def test_step_with_hint(self, make_overlay, assert_matches_snapshot):
        """Hint text renders as a smaller, grey sub-label below the step."""
        steps = [make_step(
            id="s1", act=1, zone="The Riverbank", step_number=1,
            description="Kill Renly.",
            hint="He's at the north end of the area.",
        )]
        overlay = make_overlay(steps=steps)
        assert_matches_snapshot(_grab(overlay), "step_with_hint")


class TestMultiStep:
    def test_multiple_steps_same_zone(self, make_overlay, assert_matches_snapshot):
        """Multiple steps in the same zone with no zone sub-header duplication."""
        steps = [
            make_step(id="s1", act=1, zone="The Riverbank", step_number=1,
                      description="Kill Renly."),
            make_step(id="s2", act=1, zone="The Riverbank", step_number=2,
                      description="Take the Waypoint.", tags=["mandatory"]),
            make_step(id="s3", act=1, zone="The Riverbank", step_number=3,
                      description="Proceed to Clearfell.", tags=["mandatory"]),
        ]
        overlay = make_overlay(steps=steps)
        assert_matches_snapshot(_grab(overlay), "multi_step_same_zone")

    def test_steps_across_zones(self, make_overlay, assert_matches_snapshot):
        """Steps from two zones show a zone sub-header for each group."""
        steps = [
            make_step(id="s1", act=1, zone="The Riverbank", step_number=1,
                      description="Kill Renly."),
            make_step(id="s2", act=1, zone="Clearfell", step_number=2,
                      description="Kill the Crowbell.", tags=["mandatory"]),
        ]
        overlay = make_overlay(steps=steps)
        assert_matches_snapshot(_grab(overlay), "steps_across_zones")

    def test_word_wrap_long_description(self, make_overlay, assert_matches_snapshot):
        """Long descriptions wrap correctly inside a narrow overlay."""
        steps = [make_step(
            id="s1", act=1, zone="The Riverbank", step_number=1,
            description=(
                "This is a very long step description that should wrap "
                "across multiple lines within the overlay width."
            ),
        )]
        overlay = make_overlay(
            steps=steps,
            config_overrides={"overlay.width": 260},
        )
        assert_matches_snapshot(_grab(overlay), "word_wrap_long_description")


class TestVisibilityToggles:
    def test_timer_hidden(self, make_overlay, assert_matches_snapshot):
        """Timer is hidden but exp label is visible — distinct from both-hidden."""
        steps = [make_step(zone="The Riverbank")]
        overlay = make_overlay(
            steps=steps,
            player_level=8,
            config_overrides={
                "overlay.show_timer": False,
                "overlay.show_effective_exp": True,
                "guide.character_name": "TestChar",
            },
        )
        assert_matches_snapshot(_grab(overlay), "timer_hidden")

    def test_exp_label_visible(self, make_overlay, assert_matches_snapshot):
        """Exp label renders in green when player_level is known."""
        steps = [make_step(zone="The Riverbank")]
        overlay = make_overlay(
            steps=steps,
            player_level=8,
            config_overrides={
                "overlay.show_effective_exp": True,
                "guide.character_name": "TestChar",
            },
        )
        assert_matches_snapshot(_grab(overlay), "exp_label_visible")

    def test_timer_and_exp_both_hidden(self, make_overlay, assert_matches_snapshot):
        """Overlay is more compact when both footer labels are off."""
        steps = [make_step()]
        overlay = make_overlay(
            steps=steps,
            config_overrides={
                "overlay.show_timer": False,
                "overlay.show_effective_exp": False,
            },
        )
        assert_matches_snapshot(_grab(overlay), "timer_and_exp_both_hidden")


class TestAppearance:
    def test_high_transparency(self, make_overlay, assert_matches_snapshot):
        """Near-transparent background (0.95) -- background is barely visible."""
        steps = [make_step()]
        overlay = make_overlay(
            steps=steps,
            config_overrides={"overlay.transparency": 0.95},
        )
        assert_matches_snapshot(_grab(overlay), "high_transparency")

    def test_low_transparency(self, make_overlay, assert_matches_snapshot):
        """Opaque background (0.3) -- background is clearly visible."""
        steps = [make_step()]
        overlay = make_overlay(
            steps=steps,
            config_overrides={"overlay.transparency": 0.3},
        )
        assert_matches_snapshot(_grab(overlay), "low_transparency")

    def test_large_font(self, make_overlay, assert_matches_snapshot):
        """font_size=18 -- all text scales up, layout still fits."""
        steps = [make_step()]
        overlay = make_overlay(
            steps=steps,
            config_overrides={"overlay.font_size": 18},
        )
        assert_matches_snapshot(_grab(overlay), "large_font")

    def test_narrow_width(self, make_overlay, assert_matches_snapshot):
        """width=240 -- narrowest reasonable overlay, no overflow."""
        steps = [make_step(description="Kill Renly near the Waypoint.")]
        overlay = make_overlay(
            steps=steps,
            config_overrides={"overlay.width": 240},
        )
        assert_matches_snapshot(_grab(overlay), "narrow_width")

    def test_wide_width(self, make_overlay, assert_matches_snapshot):
        """width=600 -- wide overlay, text should not stretch awkwardly."""
        steps = [make_step()]
        overlay = make_overlay(
            steps=steps,
            config_overrides={"overlay.width": 600},
        )
        assert_matches_snapshot(_grab(overlay), "wide_width")


class TestEdgeCases:
    def test_empty_guide(self, make_overlay, assert_matches_snapshot):
        """No steps loaded -- overlay renders without crashing, shows blank."""
        overlay = make_overlay(steps=[])
        assert_matches_snapshot(_grab(overlay), "empty_guide")

    def test_max_visible_lines_one(self, make_overlay, assert_matches_snapshot):
        """max_visible_lines=1 -- only one step shown even if more are available."""
        steps = [
            make_step(id=f"s{i}", step_number=i,
                      description=f"Step {i} description text.")
            for i in range(1, 6)
        ]
        overlay = make_overlay(
            steps=steps[:1],  # GuideEngine already filters; pass one step
            config_overrides={"overlay.max_visible_lines": 1},
        )
        assert_matches_snapshot(_grab(overlay), "max_visible_lines_one")
