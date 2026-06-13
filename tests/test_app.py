"""Tests for the application wiring in sin_guide.app.

Methods are exercised unbound against lightweight doubles (the same
pattern as test_main_regex_hotkeys.py) so no real QApplication, X11
display, or pynput listener is required.
"""
from __future__ import annotations

import os
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from sin_guide.app import LogWatcherThread, SinGuideApp, _configure_platform, main
from sin_guide.core.log_parser import LogEvent, LogEventType


# ---------------------------------------------------------------------------
# LogWatcherThread
# ---------------------------------------------------------------------------

def _make_watcher(path: str = "/nonexistent/Client.txt") -> LogWatcherThread:
    return LogWatcherThread(path)


class TestLogWatcherHandleEvent:
    @pytest.mark.parametrize(
        ("event_type", "data", "signal_name", "expected"),
        [
            (LogEventType.ENTERED_ZONE, "Clearfell", "zone_entered", "Clearfell"),
            (LogEventType.KILLED_BOSS, "The Devourer", "boss_killed", "The Devourer"),
            (LogEventType.QUEST_REWARD, "Skill Point", "quest_reward", "Skill Point"),
            (LogEventType.LEVEL_UP, "12", "level_up", 12),
            (LogEventType.GENERATING_AREA, "G1_1", "generating_area", "G1_1"),
        ],
    )
    def test_emits_matching_signal(self, event_type, data, signal_name, expected):
        watcher = _make_watcher()
        received: list = []
        getattr(watcher, signal_name).connect(received.append)

        watcher._handle_event(LogEvent(event_type, data, ""))

        assert received == [expected]

    def test_connecting_event_emits_connecting(self):
        watcher = _make_watcher()
        received: list = []
        watcher.connecting.connect(lambda: received.append(True))

        watcher._handle_event(LogEvent(LogEventType.CONNECTING_INSTANCE, "", ""))

        assert received == [True]

    def test_stop_clears_running_flag(self):
        watcher = _make_watcher()
        watcher.running = True
        watcher.stop()
        assert watcher.running is False


class TestLogWatcherRun:
    def _stop_after_first_sleep(self, watcher, monkeypatch):
        def fake_sleep(_seconds):
            watcher.running = False

        monkeypatch.setattr("sin_guide.app.time.sleep", fake_sleep)

    def test_reads_new_lines_and_emits_events(self, tmp_path, monkeypatch):
        client_txt = tmp_path / "Client.txt"
        client_txt.write_text(
            "2026/01/01 10:00:00 1 [SCENE] Set Source [Clearfell]\n"
            "2026/01/01 10:00:05 1 : You have reached level 5\n"
        )
        watcher = LogWatcherThread(str(client_txt))
        self._stop_after_first_sleep(watcher, monkeypatch)
        zones: list[str] = []
        levels: list[int] = []
        watcher.zone_entered.connect(zones.append)
        watcher.level_up.connect(levels.append)

        watcher.run()

        assert zones == ["Clearfell"]
        assert levels == [5]

    def test_missing_file_waits_without_raising(self, tmp_path, monkeypatch):
        watcher = LogWatcherThread(str(tmp_path / "missing.txt"))
        self._stop_after_first_sleep(watcher, monkeypatch)

        watcher.run()  # must not raise


# ---------------------------------------------------------------------------
# SinGuideApp
# ---------------------------------------------------------------------------

class TestLogPlatformInfo:
    def test_logs_platform_python_and_qt(self):
        double = SimpleNamespace()
        with patch("sin_guide.app.logger") as logger:
            SinGuideApp._log_platform_info(double)
        assert logger.info.call_count == 3


class TestInitPaths:
    def test_keeps_existing_configured_path(self, tmp_path):
        client_txt = tmp_path / "Client.txt"
        client_txt.write_text("")
        config = MagicMock()
        config.get.return_value = str(client_txt)
        double = SimpleNamespace(config=config)

        with patch("sin_guide.app.get_client_txt_path") as discover:
            SinGuideApp._init_paths(double)

        discover.assert_not_called()
        config.set.assert_not_called()

    def test_stores_discovered_path(self):
        config = MagicMock()
        config.get.return_value = ""
        double = SimpleNamespace(config=config)

        with patch(
            "sin_guide.app.get_client_txt_path", return_value="/found/Client.txt"
        ):
            SinGuideApp._init_paths(double)

        config.set.assert_called_once_with("paths.client_txt", "/found/Client.txt")

    def test_warns_when_discovery_fails(self):
        config = MagicMock()
        config.get.return_value = ""
        double = SimpleNamespace(config=config)

        with patch("sin_guide.app.get_client_txt_path", return_value=None), \
                patch("sin_guide.app.QMessageBox") as box:
            SinGuideApp._init_paths(double)

        box.warning.assert_called_once()
        config.set.assert_not_called()


class TestInitComponents:
    def test_builds_components_with_xdg_aware_export_dir(self, tmp_path):
        config = SimpleNamespace(config_dir=tmp_path)
        double = SimpleNamespace(config=config)

        with patch("sin_guide.app.WindowTracker") as tracker, \
                patch("sin_guide.app.CampaignTimer") as timer:
            SinGuideApp._init_components(double)

        # The guide must load from inside the package — guards the
        # package-data path used by the Flatpak build.
        assert len(double.guide.steps) > 0
        # Exports must follow ConfigManager's (XDG-aware) config dir, not a
        # hardcoded ~/.config.
        timer.assert_called_once_with(tmp_path / "exports")
        tracker.assert_called_once_with()
        assert double.exp_calc is not None


class TestCheckFocus:
    def _double(self, should_show: bool, focused: bool):
        tracker = MagicMock()
        tracker.game_window = None
        tracker.should_show_overlay.return_value = should_show
        overlay = MagicMock()
        overlay.winId.return_value = 42
        return SimpleNamespace(
            tracker=tracker,
            overlay=overlay,
            _game_was_focused=focused,
            _unfocus_count=0,
        )

    def test_shows_overlay_when_game_gains_focus(self):
        double = self._double(should_show=True, focused=False)

        SinGuideApp._check_focus(double)

        double.tracker.find_game_window.assert_called_once_with()
        double.overlay.show_overlay.assert_called_once_with()
        assert double._game_was_focused is True

    def test_hides_overlay_only_after_debounce(self):
        double = self._double(should_show=False, focused=True)

        for _ in range(5):
            SinGuideApp._check_focus(double)
        double.overlay.hide_overlay.assert_not_called()

        SinGuideApp._check_focus(double)
        double.overlay.hide_overlay.assert_called_once_with()
        assert double._game_was_focused is False
        assert double._unfocus_count == 0


class TestPollRaise:
    def test_no_raise_when_game_not_focused(self):
        double = SimpleNamespace(_game_was_focused=False, tracker=MagicMock())

        SinGuideApp._poll_raise(double)

        double.tracker.drain_active_window_events.assert_not_called()

    def test_schedules_raise_on_window_activity(self):
        tracker = MagicMock()
        tracker.drain_active_window_events.return_value = True
        double = SimpleNamespace(
            _game_was_focused=True, tracker=tracker, _do_raise=MagicMock()
        )

        with patch("sin_guide.app.QTimer") as qtimer:
            SinGuideApp._poll_raise(double)

        qtimer.singleShot.assert_called_once_with(30, double._do_raise)

    def test_do_raise_raises_overlay(self):
        overlay = MagicMock()
        double = SimpleNamespace(overlay=overlay)

        SinGuideApp._do_raise(double)

        overlay.raise_.assert_called_once_with()


class TestInitWatcher:
    def test_starts_watcher_when_client_txt_exists(self, tmp_path):
        client_txt = tmp_path / "Client.txt"
        client_txt.write_text("")
        config = MagicMock()
        config.get.return_value = str(client_txt)
        double = SimpleNamespace(
            config=config,
            _on_zone_entered=MagicMock(),
            _on_level_up=MagicMock(),
            _on_loading=MagicMock(),
        )

        with patch("sin_guide.app.LogWatcherThread") as thread_cls:
            SinGuideApp._init_watcher(double)

        thread_cls.assert_called_once_with(str(client_txt))
        double.watcher.start.assert_called_once_with()

    def test_no_watcher_when_client_txt_missing(self):
        config = MagicMock()
        config.get.return_value = ""
        double = SimpleNamespace(config=config)

        SinGuideApp._init_watcher(double)

        assert double.watcher is None


class TestInitRegexHotkeyDirect:
    def test_starts_listener_and_resets_flags(self):
        keyboard = MagicMock()
        double = SimpleNamespace(
            _regex_f6_pressed=True,
            _regex_f6_used_modifier=True,
            _on_regex_hotkey_press=MagicMock(),
            _on_regex_hotkey_release=MagicMock(),
        )

        SinGuideApp._init_regex_hotkey(double, keyboard)

        assert double._regex_f6_pressed is False
        assert double._regex_f6_used_modifier is False
        keyboard.Listener.return_value.start.assert_called_once_with()


class TestOnZoneEntered:
    def _double(self, *, config_values: dict, is_running: bool, is_paused: bool):
        config = MagicMock()
        config.get.side_effect = lambda key, default=None: config_values.get(
            key, default
        )
        timer = MagicMock()
        timer.state = SimpleNamespace(is_running=is_running, is_paused=is_paused)
        return SimpleNamespace(
            config=config, timer=timer, overlay=MagicMock()
        )

    def test_hideout_pauses_timer(self):
        double = self._double(
            config_values={"timer.pause_in_hideout": True},
            is_running=True,
            is_paused=False,
        )

        SinGuideApp._on_zone_entered(double, "Hideout")

        double.overlay.handle_zone_enter.assert_called_once_with("Hideout")
        double.timer.pause.assert_called_once_with()
        double.timer.start.assert_not_called()

    def test_first_zone_starts_timer(self):
        double = self._double(config_values={}, is_running=False, is_paused=False)

        SinGuideApp._on_zone_entered(double, "Clearfell")

        double.timer.start.assert_called_once_with()

    def test_paused_timer_resumes_and_act_advances(self):
        double = self._double(
            config_values={"guide.character_name": "Sin"},
            is_running=True,
            is_paused=True,
        )

        SinGuideApp._on_zone_entered(double, "Act 2: Vastiri Outskirts")

        double.timer.resume.assert_called_once_with()
        double.timer.advance_act.assert_called_once_with("Sin")


class TestSimpleHandlers:
    def test_on_level_up_forwards_to_overlay(self):
        double = SimpleNamespace(overlay=MagicMock())
        SinGuideApp._on_level_up(double, 42)
        double.overlay.handle_level_up.assert_called_once_with(42)

    def test_on_loading_pauses_timer(self):
        double = SimpleNamespace(timer=MagicMock())
        SinGuideApp._on_loading(double)
        double.timer.pause.assert_called_once_with()

    def test_step_and_scan_hotkeys_forward_to_overlay(self):
        double = SimpleNamespace(overlay=MagicMock())
        SinGuideApp._on_prev_hotkey(double)
        SinGuideApp._on_next_hotkey(double)
        SinGuideApp._on_scan_gems(double)
        double.overlay._on_prev.assert_called_once_with()
        double.overlay._on_next.assert_called_once_with()
        double.overlay.scan_gems.assert_called_once_with()


class TestShowSettings:
    def test_opens_panel_and_reloads_overlay_config(self):
        double = SimpleNamespace(
            config=MagicMock(), regex_manager=MagicMock(), overlay=MagicMock()
        )

        with patch("sin_guide.app.SettingsPanel") as panel_cls:
            SinGuideApp.show_settings(double)

        panel_cls.assert_called_once_with(
            double.config, regex_manager=double.regex_manager
        )
        panel_cls.return_value.exec.assert_called_once_with()
        double.overlay.reload_config.assert_called_once_with()


class TestRun:
    def test_run_delegates_to_qapplication_exec(self):
        app = MagicMock()
        app.exec.return_value = 7
        double = SimpleNamespace(app=app)

        assert SinGuideApp.run(double) == 7


class TestCleanupFull:
    def test_stops_all_components(self):
        double = SimpleNamespace(
            _focus_timer=MagicMock(),
            _raise_timer=MagicMock(),
            watcher=MagicMock(),
            hotkey_listener=MagicMock(),
            _regex_listener=MagicMock(),
            tracker=MagicMock(),
        )

        SinGuideApp.cleanup(double)

        double._focus_timer.stop.assert_called_once_with()
        double._raise_timer.stop.assert_called_once_with()
        double.watcher.stop.assert_called_once_with()
        double.watcher.wait.assert_called_once_with(2000)
        double.hotkey_listener.stop.assert_called_once_with()
        double._regex_listener.stop.assert_called_once_with()
        double.tracker.cleanup.assert_called_once_with()

    def test_tolerates_absent_components(self):
        double = SimpleNamespace(
            watcher=None, hotkey_listener=None, tracker=MagicMock()
        )

        SinGuideApp.cleanup(double)

        double.tracker.cleanup.assert_called_once_with()


# ---------------------------------------------------------------------------
# Module-level entry points
# ---------------------------------------------------------------------------

class TestConfigurePlatform:
    def test_defaults_to_xcb(self, monkeypatch):
        monkeypatch.delenv("QT_QPA_PLATFORM", raising=False)
        _configure_platform()
        assert os.environ["QT_QPA_PLATFORM"] == "xcb"

    def test_respects_existing_value(self, monkeypatch):
        monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
        _configure_platform()
        assert os.environ["QT_QPA_PLATFORM"] == "offscreen"


class TestMain:
    def test_runs_app_and_exits_with_return_code(self, monkeypatch):
        monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
        app = MagicMock()
        app.run.return_value = 3

        with patch("sin_guide.app.SinGuideApp", return_value=app):
            with pytest.raises(SystemExit) as exc_info:
                main()

        assert exc_info.value.code == 3
        app.cleanup.assert_called_once_with()
