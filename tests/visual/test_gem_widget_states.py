"""Visual regression tests for GemWidget states."""
from __future__ import annotations

from PySide6.QtWidgets import QApplication

from sin_guide.utils.pob_parser import GemSetup

from tests.test_gem_widget import GEM_DB


def _grab(widget):
    QApplication.processEvents()
    return widget.grab()


class TestGemRenderStates:
    def test_build_with_available_and_upcoming(self, qtbot, assert_matches_snapshot):
        from sin_guide.overlay.gem_widget import GemWidget

        widget = GemWidget(GEM_DB)
        qtbot.addWidget(widget)
        widget.show()
        qtbot.waitExposed(widget)

        gems = [
            GemSetup("Fireball", 1, []),
            GemSetup("Frostbolt", 1, []),
            GemSetup("Ice Nova", 1, []),
        ]
        widget.set_build(gems)
        widget.set_player_level(3)

        assert_matches_snapshot(_grab(widget), "gem_available_and_upcoming")

    def test_scan_result_with_needed_and_extra(self, qtbot, assert_matches_snapshot):
        from sin_guide.overlay.gem_widget import GemWidget

        widget = GemWidget(GEM_DB)
        qtbot.addWidget(widget)
        widget.show()
        qtbot.waitExposed(widget)

        gems = [GemSetup("Fireball", 1, []), GemSetup("Ice Nova", 1, [])]
        widget.set_build(gems)
        widget.set_scan_result({
            "available": ["Fireball", "Frostbolt", "Spark"],
            "needed": ["Fireball"],
        })

        assert_matches_snapshot(_grab(widget), "gem_scan_result")

    def test_build_without_level_shows_prompt(self, qtbot, assert_matches_snapshot):
        from sin_guide.overlay.gem_widget import GemWidget

        widget = GemWidget(GEM_DB)
        qtbot.addWidget(widget)
        widget.show()
        qtbot.waitExposed(widget)

        gems = [GemSetup("Fireball", 1, [])]
        widget.set_build(gems)

        assert_matches_snapshot(_grab(widget), "gem_no_level_prompt")
