"""Tests for the F6 regex hotkey callbacks in main.py."""
from __future__ import annotations

from types import SimpleNamespace
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
        self._regex_f6_pressed = False
        self._regex_f6_used_modifier = False


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


def _keyboard_mock() -> SimpleNamespace:
    return SimpleNamespace(
        Key=SimpleNamespace(
            f6="f6", up="up", down="down", other="other"
        )
    )


class TestOnRegexHotkeyPress:
    def test_f6_press_sets_pressed_flag(self) -> None:
        keyboard = _keyboard_mock()
        double = _AppDouble(MagicMock(), MagicMock())

        SinGuideApp._on_regex_hotkey_press(double, keyboard.Key.f6, keyboard)

        assert double._regex_f6_pressed is True
        assert double._regex_f6_used_modifier is False

    def test_f6_press_resets_modifier_flag(self) -> None:
        keyboard = _keyboard_mock()
        double = _AppDouble(MagicMock(), MagicMock())
        double._regex_f6_pressed = True
        double._regex_f6_used_modifier = True

        SinGuideApp._on_regex_hotkey_press(double, keyboard.Key.f6, keyboard)

        assert double._regex_f6_pressed is True
        assert double._regex_f6_used_modifier is False

    def test_up_while_f6_pressed_queues_next_and_sets_modifier(self) -> None:
        keyboard = _keyboard_mock()
        double = _AppDouble(MagicMock(), MagicMock())
        double._regex_f6_pressed = True
        double._on_regex_next = MagicMock()

        with patch("main.QTimer.singleShot") as single_shot:
            SinGuideApp._on_regex_hotkey_press(
                double, keyboard.Key.up, keyboard
            )

        assert double._regex_f6_used_modifier is True
        single_shot.assert_called_once()
        assert single_shot.call_args.args[1] is double._on_regex_next

    def test_down_while_f6_pressed_queues_prev_and_sets_modifier(self) -> None:
        keyboard = _keyboard_mock()
        double = _AppDouble(MagicMock(), MagicMock())
        double._regex_f6_pressed = True
        double._on_regex_prev = MagicMock()

        with patch("main.QTimer.singleShot") as single_shot:
            SinGuideApp._on_regex_hotkey_press(
                double, keyboard.Key.down, keyboard
            )

        assert double._regex_f6_used_modifier is True
        single_shot.assert_called_once()
        assert single_shot.call_args.args[1] is double._on_regex_prev

    def test_arrows_ignored_when_f6_not_pressed(self) -> None:
        keyboard = _keyboard_mock()
        double = _AppDouble(MagicMock(), MagicMock())
        double._regex_f6_pressed = False

        with patch("main.QTimer.singleShot") as single_shot:
            SinGuideApp._on_regex_hotkey_press(
                double, keyboard.Key.up, keyboard
            )
            SinGuideApp._on_regex_hotkey_press(
                double, keyboard.Key.down, keyboard
            )

        single_shot.assert_not_called()
        assert double._regex_f6_used_modifier is False

    def test_exception_is_swallowed(self) -> None:
        keyboard = _keyboard_mock()
        double = _AppDouble(MagicMock(), MagicMock())
        double._regex_f6_pressed = True

        with patch("main.QTimer.singleShot", side_effect=RuntimeError):
            SinGuideApp._on_regex_hotkey_press(
                double, keyboard.Key.up, keyboard
            )


class TestOnRegexHotkeyRelease:
    def test_f6_release_after_plain_press_queues_copy(self) -> None:
        keyboard = _keyboard_mock()
        double = _AppDouble(MagicMock(), MagicMock())
        double._regex_f6_pressed = True
        double._regex_f6_used_modifier = False
        double._on_regex_copy = MagicMock()

        with patch("main.QTimer.singleShot") as single_shot:
            SinGuideApp._on_regex_hotkey_release(
                double, keyboard.Key.f6, keyboard
            )

        single_shot.assert_called_once()
        assert single_shot.call_args.args[1] is double._on_regex_copy
        assert double._regex_f6_pressed is False

    def test_f6_release_after_modifier_skips_copy(self) -> None:
        keyboard = _keyboard_mock()
        double = _AppDouble(MagicMock(), MagicMock())
        double._regex_f6_pressed = True
        double._regex_f6_used_modifier = True

        with patch("main.QTimer.singleShot") as single_shot:
            SinGuideApp._on_regex_hotkey_release(
                double, keyboard.Key.f6, keyboard
            )

        single_shot.assert_not_called()
        assert double._regex_f6_pressed is False

    def test_f6_release_when_not_pressed_still_clears_flag(self) -> None:
        keyboard = _keyboard_mock()
        double = _AppDouble(MagicMock(), MagicMock())
        double._regex_f6_pressed = False
        double._regex_f6_used_modifier = True

        with patch("main.QTimer.singleShot") as single_shot:
            SinGuideApp._on_regex_hotkey_release(
                double, keyboard.Key.f6, keyboard
            )

        single_shot.assert_not_called()
        assert double._regex_f6_pressed is False

    def test_non_f6_release_is_noop(self) -> None:
        keyboard = _keyboard_mock()
        double = _AppDouble(MagicMock(), MagicMock())
        double._regex_f6_pressed = True

        with patch("main.QTimer.singleShot") as single_shot:
            SinGuideApp._on_regex_hotkey_release(
                double, keyboard.Key.other, keyboard
            )

        single_shot.assert_not_called()
        assert double._regex_f6_pressed is True

    def test_exception_is_swallowed(self) -> None:
        keyboard = _keyboard_mock()
        double = _AppDouble(MagicMock(), MagicMock())
        double._regex_f6_pressed = True
        double._regex_f6_used_modifier = False

        with patch("main.QTimer.singleShot", side_effect=RuntimeError):
            SinGuideApp._on_regex_hotkey_release(
                double, keyboard.Key.f6, keyboard
            )

        assert double._regex_f6_pressed is False

