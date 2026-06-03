"""Unit tests for RegexWidget — show/hide behaviour, text format, and auto-hide."""
from __future__ import annotations

import pytest
from PySide6.QtCore import Qt

from sin_guide.core.regex_manager import RegexEntry
from sin_guide.overlay.regex_widget import RegexWidget


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def widget(qtbot):
    w = RegexWidget()
    qtbot.addWidget(w)
    return w


def _entry(name: str = "Maps", pattern: str = "map") -> RegexEntry:
    return RegexEntry(name=name, pattern=pattern, created_at="2024-01-01T00:00:00+00:00")


# ---------------------------------------------------------------------------
# Initialisation
# ---------------------------------------------------------------------------


class TestInit:
    def test_widget_starts_hidden(self, widget) -> None:
        assert widget.isVisible() is False

    def test_widget_is_centre_aligned(self, widget) -> None:
        assert widget.alignment() == Qt.AlignmentFlag.AlignCenter

    def test_widget_has_word_wrap_enabled(self, widget) -> None:
        assert widget.wordWrap() is True

    def test_widget_exposes_display_duration_constant(self, widget) -> None:
        assert RegexWidget.DISPLAY_DURATION_MS == 1500


# ---------------------------------------------------------------------------
# show_regex — with a RegexEntry
# ---------------------------------------------------------------------------


class TestShowRegex:
    def test_show_regex_displays_label_and_name(self, widget) -> None:
        widget.show_regex(_entry("Maps"))
        assert widget.isVisible() is True
        assert widget.text() == "[Regex] Maps"

    def test_show_regex_uses_bracketed_prefix(self, widget) -> None:
        widget.show_regex(_entry("Essences"))
        text = widget.text()
        for ch in text:
            assert ord(ch) < 0x2600, f"Found emoji-like char U+{ord(ch):04X} in label"

    def test_show_regex_uses_getattr_fallback(self, widget) -> None:
        class Fake:
            def __str__(self) -> str:
                return "fallback-name"

        widget.show_regex(Fake())
        assert widget.text() == "[Regex] fallback-name"


# ---------------------------------------------------------------------------
# show_regex — None / hide path
# ---------------------------------------------------------------------------


class TestHide:
    def test_show_regex_with_none_hides_widget(self, widget) -> None:
        widget.show_regex(_entry("Anything"))
        assert widget.isVisible() is True

        widget.show_regex(None)
        assert widget.isVisible() is False

    def test_show_regex_with_none_when_already_hidden(self, widget) -> None:
        assert widget.isVisible() is False
        widget.show_regex(None)
        assert widget.isVisible() is False


# ---------------------------------------------------------------------------
# Auto-hide timer
# ---------------------------------------------------------------------------


class TestAutoHide:
    def test_widget_hides_after_display_duration(self, qtbot, widget) -> None:
        widget.show_regex(_entry("Maps"))
        assert widget.isVisible() is True

        qtbot.wait(widget.DISPLAY_DURATION_MS + 300)
        assert widget.isVisible() is False

    def test_repeated_show_overwrites_text(self, widget) -> None:
        widget.show_regex(_entry("A"))
        first_text = widget.text()

        widget.show_regex(_entry("B"))
        assert widget.text() != first_text
        assert widget.text() == "[Regex] B"

    def test_rapid_show_resets_hide_timer(self, widget) -> None:
        """A second show_regex call must restart the auto-hide timer so
        the new entry stays visible for the full duration rather than
        being hidden by the queued hide from the first call.
        """
        widget.show_regex(_entry("A"))
        widget.show_regex(_entry("B"))

        assert widget.isVisible() is True
        remaining = widget._hide_timer.remainingTime()
        assert remaining > widget.DISPLAY_DURATION_MS - 100, (
            f"Timer not reset: remainingTime={remaining}ms "
            f"(expected >{widget.DISPLAY_DURATION_MS - 100}ms)"
        )

    def test_show_none_cancels_pending_hide(self, widget) -> None:
        widget.show_regex(_entry("A"))
        assert widget._hide_timer.isActive() is True

        widget.show_regex(None)

        assert widget.isVisible() is False
        assert widget._hide_timer.isActive() is False
