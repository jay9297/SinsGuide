"""Tests for the F6 regex hotkey callbacks in main.py."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

from sin_guide.core.regex_manager import RegexEntry
from main import SinGuideApp


def _entry(name: str = "Maps", pattern: str = "map") -> RegexEntry:
    return RegexEntry(
        name=name, pattern=pattern, created_at="2024-01-01T00:00:00+00:00"
    )


class _AppDouble:
    def __init__(self, regex_manager, overlay):
        self.regex_manager = regex_manager
        self.overlay = overlay


class TestOnRegexCopy:
    def test_copies_current_pattern_to_clipboard(self) -> None:
        entry = _entry()
        manager = MagicMock()
        manager.get_current.return_value = entry
        overlay = MagicMock()
        double = _AppDouble(manager, overlay)

        with patch("main.QApplication.clipboard") as clipboard:
            SinGuideApp._on_regex_copy(double)

        manager.get_current.assert_called_once_with()
        clipboard.return_value.setText.assert_called_once_with("map")
        overlay.show_regex_feedback.assert_called_once_with(entry)

    def test_no_clipboard_write_when_no_current_entry(self) -> None:
        manager = MagicMock()
        manager.get_current.return_value = None
        overlay = MagicMock()
        double = _AppDouble(manager, overlay)

        with patch("main.QApplication.clipboard") as clipboard:
            SinGuideApp._on_regex_copy(double)

        clipboard.return_value.setText.assert_not_called()
        overlay.show_regex_feedback.assert_called_once_with(None)


class TestOnRegexNext:
    def test_advances_and_shows_feedback(self) -> None:
        entry = _entry()
        manager = MagicMock()
        manager.next_regex.return_value = entry
        overlay = MagicMock()
        double = _AppDouble(manager, overlay)

        SinGuideApp._on_regex_next(double)

        manager.next_regex.assert_called_once_with()
        overlay.show_regex_feedback.assert_called_once_with(entry)

    def test_handles_empty_collection(self) -> None:
        manager = MagicMock()
        manager.next_regex.return_value = None
        overlay = MagicMock()
        double = _AppDouble(manager, overlay)

        SinGuideApp._on_regex_next(double)

        overlay.show_regex_feedback.assert_called_once_with(None)


class TestOnRegexPrev:
    def test_retreats_and_shows_feedback(self) -> None:
        entry = _entry()
        manager = MagicMock()
        manager.prev_regex.return_value = entry
        overlay = MagicMock()
        double = _AppDouble(manager, overlay)

        SinGuideApp._on_regex_prev(double)

        manager.prev_regex.assert_called_once_with()
        overlay.show_regex_feedback.assert_called_once_with(entry)

    def test_handles_empty_collection(self) -> None:
        manager = MagicMock()
        manager.prev_regex.return_value = None
        overlay = MagicMock()
        double = _AppDouble(manager, overlay)

        SinGuideApp._on_regex_prev(double)

        overlay.show_regex_feedback.assert_called_once_with(None)
