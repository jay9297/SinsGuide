"""Tests for GemWidget — gem availability display widget."""
from __future__ import annotations

from PySide6.QtWidgets import QLabel

from sin_guide.utils.pob_parser import GemSetup

GEM_DB = {
    "fireball": {"type": "skill", "level": 3, "attribute": 3},
    "frostbolt": {"type": "skill", "level": 5, "attribute": 3},
    "spark": {"type": "skill", "level": 4, "attribute": 3},
    "ice nova": {"type": "skill", "level": 6, "attribute": 3},
    "herald of ice": {"type": "spirit", "level": 4, "attribute": 3},
    "brutality i": {"type": "support", "level": 1, "attribute": 1},
}


class TestEmptyState:
    """GemWidget with no build loaded."""

    def test_has_content_false_when_no_build(self, qtbot):
        """When no build is loaded, has_content returns False."""
        from sin_guide.overlay.gem_widget import GemWidget

        widget = GemWidget(GEM_DB)
        qtbot.addWidget(widget)

        assert widget.has_content is False

    def test_layout_empty_when_no_build(self, qtbot):
        """When no build is loaded, the layout contains no child widgets."""
        from sin_guide.overlay.gem_widget import GemWidget

        widget = GemWidget(GEM_DB)
        qtbot.addWidget(widget)

        assert widget._content_layout.count() == 0


def _label_texts(widget) -> list[str]:
    """Return text from all QLabels in the widget's content layout."""
    texts = []
    for i in range(widget._content_layout.count()):
        item = widget._content_layout.itemAt(i)
        if item and isinstance(item.widget(), QLabel):
            texts.append(item.widget().text())
    return texts


class TestBuildWithLevel:
    """GemWidget with build loaded and player level set."""

    def test_shows_available_gems_with_checkmark(self, qtbot):
        """Gems at or below player level show green ✓ prefix."""
        from sin_guide.overlay.gem_widget import GemWidget

        widget = GemWidget(GEM_DB)
        qtbot.addWidget(widget)

        gems = [GemSetup("Fireball", 1, []), GemSetup("Spark", 1, [])]
        widget.set_build(gems)
        widget.set_player_level(4)

        texts = _label_texts(widget)
        assert any("Fireball" in t for t in texts)
        assert any("Spark" in t for t in texts)
        assert any(t.startswith("  ✓") for t in texts)

    def test_shows_upcoming_gems_with_tilde(self, qtbot):
        """Gems above player level but within horizon show yellow ~ prefix."""
        from sin_guide.overlay.gem_widget import GemWidget

        widget = GemWidget(GEM_DB)
        qtbot.addWidget(widget)

        gems = [
            GemSetup("Fireball", 1, []),
            GemSetup("Ice Nova", 1, []),
        ]
        widget.set_build(gems)
        widget.set_player_level(3)

        texts = _label_texts(widget)
        assert any("Fireball" in t for t in texts)  # available at L3
        assert any("Ice Nova" in t for t in texts)  # upcoming at L6
        assert any(t.startswith("  ~") for t in texts)

    def test_gems_with_unknown_level_not_shown(self, qtbot):
        """Gems not in the database are silently skipped."""
        from sin_guide.overlay.gem_widget import GemWidget

        widget = GemWidget(GEM_DB)
        qtbot.addWidget(widget)

        gems = [GemSetup("UnknownGem", 1, [])]
        widget.set_build(gems)
        widget.set_player_level(10)

        texts = _label_texts(widget)
        assert "UnknownGem" not in texts

    def test_renders_in_expected_order(self, qtbot):
        """Available gems render before upcoming gems."""
        from sin_guide.overlay.gem_widget import GemWidget

        widget = GemWidget(GEM_DB)
        qtbot.addWidget(widget)

        gems = [
            GemSetup("Ice Nova", 1, []),     # L6 — upcoming
            GemSetup("Fireball", 1, []),     # L3 — available
        ]
        widget.set_build(gems)
        widget.set_player_level(3)

        texts = _label_texts(widget)
        fireball_idx = next(i for i, t in enumerate(texts) if "Fireball" in t)
        ice_nova_idx = next(i for i, t in enumerate(texts) if "Ice Nova" in t)
        assert fireball_idx < ice_nova_idx


class TestScanResult:
    """GemWidget showing OCR scan results."""

    def test_needed_gem_shows_green_check(self, qtbot):
        """Gem in both scan result and build shows green ✓."""
        from sin_guide.overlay.gem_widget import GemWidget

        widget = GemWidget(GEM_DB)
        qtbot.addWidget(widget)

        gems = [GemSetup("Fireball", 1, [])]
        widget.set_build(gems)
        widget.set_scan_result({
            "available": ["Fireball"],
            "needed": ["Fireball"],
        })

        texts = _label_texts(widget)
        needed_labels = [t for t in texts if "Fireball" in t]
        assert len(needed_labels) == 1
        assert needed_labels[0].startswith("  ✓")

    def test_extra_gem_shows_red_cross(self, qtbot):
        """Gem in scan but not in build shows red ✗."""
        from sin_guide.overlay.gem_widget import GemWidget

        widget = GemWidget(GEM_DB)
        qtbot.addWidget(widget)

        gems = [GemSetup("Fireball", 1, [])]
        widget.set_build(gems)
        widget.set_scan_result({
            "available": ["Fireball", "Frostbolt"],
            "needed": ["Fireball"],
        })

        texts = _label_texts(widget)
        frostbolt_label = [t for t in texts if "Frostbolt" in t]
        assert len(frostbolt_label) == 1
        assert frostbolt_label[0].startswith("  ✗")

    def test_scan_result_overrides_level_display(self, qtbot):
        """When scan result is set, it renders instead of level-based gems."""
        from sin_guide.overlay.gem_widget import GemWidget

        widget = GemWidget(GEM_DB)
        qtbot.addWidget(widget)

        gems = [GemSetup("Fireball", 1, [])]
        widget.set_build(gems)
        widget.set_player_level(4)
        widget.set_scan_result({
            "available": ["Fireball"],
            "needed": ["Fireball"],
        })

        texts = _label_texts(widget)
        assert any("Fireball" in t for t in texts)


class TestHasContent:
    """has_content property behavior."""

    def test_true_after_set_build(self, qtbot):
        from sin_guide.overlay.gem_widget import GemWidget

        widget = GemWidget(GEM_DB)
        qtbot.addWidget(widget)

        widget.set_build([GemSetup("Fireball", 1, [])])
        assert widget.has_content is True

    def test_false_after_clearing_build(self, qtbot):
        from sin_guide.overlay.gem_widget import GemWidget

        widget = GemWidget(GEM_DB)
        qtbot.addWidget(widget)

        widget.set_build([GemSetup("Fireball", 1, [])])
        widget.set_build([])
        assert widget.has_content is False

    def test_layout_cleared_when_build_cleared(self, qtbot):
        from sin_guide.overlay.gem_widget import GemWidget

        widget = GemWidget(GEM_DB)
        qtbot.addWidget(widget)

        widget.set_build([GemSetup("Fireball", 1, [])])
        widget.set_player_level(4)
        assert widget._content_layout.count() > 0

        widget.set_build([])
        assert widget._content_layout.count() == 0


class TestImportBuild:
    """import_build() URL parsing and build loading."""

    def test_invalid_url_returns_false(self, qtbot):
        """Non-pobb.in URLs return False without changing build state."""
        from sin_guide.overlay.gem_widget import GemWidget

        widget = GemWidget(GEM_DB)
        qtbot.addWidget(widget)

        result = widget.import_build("not-a-valid-pob-url")
        assert result is False
        assert widget.has_content is False

    def test_empty_url_returns_false(self, qtbot):
        from sin_guide.overlay.gem_widget import GemWidget

        widget = GemWidget(GEM_DB)
        qtbot.addWidget(widget)

        result = widget.import_build("")
        assert result is False
        assert widget.has_content is False
