"""Tests for the F6 regex hotkey callbacks in main.py."""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

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


class _HotkeyAppDouble:
    """Minimal stand-in for ``SinGuideApp`` to exercise ``_init_hotkeys``."""

    def __init__(self) -> None:
        self.config = MagicMock()
        self.config.get.side_effect = lambda key, default: default
        self._on_prev_hotkey = MagicMock()
        self._on_next_hotkey = MagicMock()
        self._on_scan_gems = MagicMock()
        self.hotkey_listener: object | None = None

    def _init_regex_hotkey(self, keyboard) -> None:
        raise RuntimeError("simulated regex hotkey init failure")


def _pynput_keyboard_mock() -> MagicMock:
    """Build a MagicMock matching the small slice of pynput.keyboard we use."""
    keyboard = MagicMock()
    keyboard.Key = SimpleNamespace(f6="f6", up="up", down="down")
    return keyboard


class TestInitHotkeys:
    def test_regex_init_failure_stops_primary_listener(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """If ``_init_regex_hotkey`` raises, the primary GlobalHotKeys
        listener must be stopped and ``hotkey_listener`` set to ``None``
        so that ``cleanup()`` does not orphan a running background thread.
        """
        import sys
        import types

        keyboard = _pynput_keyboard_mock()
        keyboard.GlobalHotKeys.return_value = MagicMock()
        keyboard.Listener.return_value = MagicMock()

        fake_pynput = types.ModuleType("pynput")
        fake_pynput.keyboard = keyboard
        monkeypatch.setitem(sys.modules, "pynput", fake_pynput)
        monkeypatch.setitem(sys.modules, "pynput.keyboard", keyboard)
        monkeypatch.setattr("main.logger", MagicMock())

        app = _HotkeyAppDouble()

        SinGuideApp._init_hotkeys(app)

        primary = keyboard.GlobalHotKeys.return_value
        primary.start.assert_called_once_with()
        primary.stop.assert_called_once_with()
        assert app.hotkey_listener is None

    def test_primary_listener_construction_failure_does_not_set_attribute(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """If the primary GlobalHotKeys listener fails to start, the
        attribute is cleared so cleanup() is a no-op rather than
        touching a half-constructed listener.
        """
        import sys
        import types

        keyboard = _pynput_keyboard_mock()
        keyboard.GlobalHotKeys.return_value.start.side_effect = RuntimeError(
            "boom"
        )

        fake_pynput = types.ModuleType("pynput")
        fake_pynput.keyboard = keyboard
        monkeypatch.setitem(sys.modules, "pynput", fake_pynput)
        monkeypatch.setitem(sys.modules, "pynput.keyboard", keyboard)
        monkeypatch.setattr("main.logger", MagicMock())

        app = _HotkeyAppDouble()

        SinGuideApp._init_hotkeys(app)

        assert app.hotkey_listener is None


class TestCleanup:
    def test_cleanup_stops_regex_listener_when_set(self) -> None:
        """cleanup() must call stop() on _regex_listener when it is set."""

        class _CleanupDouble:
            watcher = None
            hotkey_listener = None
            tracker = MagicMock()

        double = _CleanupDouble()
        double._regex_listener = MagicMock()

        SinGuideApp.cleanup(double)

        double._regex_listener.stop.assert_called_once()

    def test_cleanup_skips_regex_listener_when_not_set(self) -> None:
        """cleanup() must not crash when _regex_listener was never assigned."""

        class _CleanupDouble:
            watcher = None
            hotkey_listener = None
            tracker = MagicMock()

        double = _CleanupDouble()
        # _regex_listener deliberately not set to simulate pynput import failure
        SinGuideApp.cleanup(double)  # must not raise
