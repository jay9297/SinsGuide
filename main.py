import logging
import platform
import sys
import os
from pathlib import Path
import threading
import time

logger = logging.getLogger(__name__)

from PySide6.QtCore import QObject, Signal, QThread, QTimer
from PySide6.QtCore import qVersion as qt_version
from PySide6.QtWidgets import QApplication, QMessageBox

from typing import Any

from sin_guide.config.manager import ConfigManager
from sin_guide.core.guide_engine import GuideEngine
from sin_guide.core.log_parser import LogParser, LogEventType
from sin_guide.core.regex_manager import RegexManager
from sin_guide.core.timer import CampaignTimer
from sin_guide.core.exp_calculator import ExpCalculator
from sin_guide.overlay.main_window import OverlayWindow
from sin_guide.overlay.settings_panel import SettingsPanel
from sin_guide.overlay.window_tracker import WindowTracker
from sin_guide.utils.steam_discovery import get_client_txt_path


class LogWatcherThread(QThread):
    zone_entered = Signal(str)
    boss_killed = Signal(str)
    quest_reward = Signal(str)
    level_up = Signal(int)
    generating_area = Signal(str)
    connecting = Signal()

    def __init__(self, client_txt_path: str):
        super().__init__()
        self.client_txt_path = client_txt_path
        self.running = False
        self.parser = LogParser()

    def run(self):
        self.running = True
        last_size = 0
        while self.running:
            try:
                if not os.path.exists(self.client_txt_path):
                    time.sleep(1)
                    continue
                current_size = os.path.getsize(self.client_txt_path)
                if current_size < last_size:
                    last_size = 0
                if current_size > last_size:
                    with open(self.client_txt_path, "r", encoding="utf-8", errors="ignore") as f:
                        f.seek(last_size)
                        for line in f:
                            event = self.parser.parse_line(line.strip())
                            if event:
                                self._handle_event(event)
                    last_size = current_size
            except Exception as e:
                logger.error("LogWatcher error: %s", e, exc_info=True)
            time.sleep(0.5)

    def _handle_event(self, event):
        if event.event_type == LogEventType.ENTERED_ZONE:
            logger.debug("Parsed zone enter: '%s'", event.data)
            self.zone_entered.emit(event.data)
        elif event.event_type == LogEventType.KILLED_BOSS:
            self.boss_killed.emit(event.data)
        elif event.event_type == LogEventType.QUEST_REWARD:
            self.quest_reward.emit(event.data)
        elif event.event_type == LogEventType.LEVEL_UP:
            self.level_up.emit(int(event.data))
        elif event.event_type == LogEventType.GENERATING_AREA:
            self.generating_area.emit(event.data)
        elif event.event_type == LogEventType.CONNECTING_INSTANCE:
            self.connecting.emit()

    def stop(self):
        self.running = False


class SinGuideApp(QObject):
    def __init__(self):
        super().__init__()
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)
        self._log_platform_info()
        self.config = ConfigManager()
        self.regex_manager = RegexManager(self.config)
        self._init_paths()
        self._init_components()
        self._init_overlay()
        self._init_watcher()
        self._init_hotkeys()

    def _log_platform_info(self) -> None:
        logger = logging.getLogger(__name__)
        logger.info("Platform: %s", platform.system())
        logger.info("Python: %s", platform.python_version())
        logger.info("PySide6/Qt: %s", qt_version())

    def _init_paths(self):
        client_txt = self.config.get("paths.client_txt", "")
        if not client_txt or not os.path.exists(client_txt):
            discovered = get_client_txt_path()
            if discovered:
                self.config.set("paths.client_txt", discovered)
            else:
                QMessageBox.warning(
                    None,
                    "Sin's Guide",
                    "Could not find Client.txt automatically.\n"
                    "Please set the path in Settings.",
                )

    def _init_components(self):
        guide_path = Path(__file__).parent / "data" / "guides" / "poe2_campaign.json"
        self.guide = GuideEngine(guide_path)
        self.timer = CampaignTimer(Path.home() / ".config" / "sin_guide" / "exports")
        self.exp_calc = ExpCalculator()
        self.tracker = WindowTracker()

    def _init_overlay(self):
        self.overlay = OverlayWindow(self.config, self.guide, self.timer, self.exp_calc)
        self.overlay.on_settings_requested = self.show_settings
        self.overlay.hide_overlay()
        self.tracker.subscribe_to_active_window_changes()
        self._focus_timer = QTimer(self)
        self._focus_timer.timeout.connect(self._check_focus)
        self._focus_timer.start(500)
        self._raise_timer = QTimer(self)
        self._raise_timer.timeout.connect(self._poll_raise)
        self._raise_timer.start(50)
        self._game_was_focused = False
        self._unfocus_count = 0

    def _check_focus(self):
        if not self.tracker.game_window:
            self.tracker.find_game_window()
        
        overlay_id = int(self.overlay.winId()) if self.overlay else None
        should_show = self.tracker.should_show_overlay(overlay_id)
        
        if should_show and not self._game_was_focused:
            self._game_was_focused = True
            self._unfocus_count = 0
            self.overlay.show_overlay()
        elif not should_show and self._game_was_focused:
            self._unfocus_count += 1
            if self._unfocus_count >= 6:
                self._game_was_focused = False
                self._unfocus_count = 0
                self.overlay.hide_overlay()

    def _poll_raise(self):
        if not self._game_was_focused:
            return
        if self.tracker.drain_active_window_events():
            QTimer.singleShot(30, self._do_raise)

    def _do_raise(self):
        self.overlay.raise_()

    def _init_watcher(self):
        client_txt = self.config.get("paths.client_txt", "")
        if client_txt and os.path.exists(client_txt):
            self.watcher = LogWatcherThread(client_txt)
            self.watcher.zone_entered.connect(self._on_zone_entered)
            self.watcher.level_up.connect(self._on_level_up)
            self.watcher.connecting.connect(self._on_loading)
            self.watcher.start()
        else:
            self.watcher = None

    def _init_hotkeys(self):
        try:
            from pynput import keyboard

            self.hotkey_listener = keyboard.GlobalHotKeys({
                self.config.get("hotkeys.prev_step", "f3"): self._on_prev_hotkey,
                self.config.get("hotkeys.next_step", "f4"): self._on_next_hotkey,
                "<f5>": self._on_scan_gems,
            })
            self.hotkey_listener.start()

            self._init_regex_hotkey(keyboard)
        except Exception:
            self.hotkey_listener = None

    def _init_regex_hotkey(self, keyboard: Any) -> None:
        """Set up F6 hotkey for regex copy (release) and cycling (hold + Up/Down).

        Uses a separate ``keyboard.Listener`` so we can detect F6 key-release
        (copy to clipboard) vs. F6+Up/Down (cycle entries).  The existing
        ``GlobalHotKeys`` fires on press, which is insufficient for the
        dual-purpose F6 key.
        """
        self._regex_f6_pressed = False
        self._regex_f6_used_modifier = False

        def on_press(key: Any) -> None:
            try:
                if key == keyboard.Key.f6:
                    self._regex_f6_pressed = True
                    self._regex_f6_used_modifier = False
                elif self._regex_f6_pressed:
                    if key == keyboard.Key.up:
                        self._regex_f6_used_modifier = True
                        QTimer.singleShot(0, self._on_regex_next)
                    elif key == keyboard.Key.down:
                        self._regex_f6_used_modifier = True
                        QTimer.singleShot(0, self._on_regex_prev)
            except Exception:
                logger.debug("Regex hotkey press error", exc_info=True)

        def on_release(key: Any) -> None:
            try:
                if key == keyboard.Key.f6:
                    if self._regex_f6_pressed and not self._regex_f6_used_modifier:
                        QTimer.singleShot(0, self._on_regex_copy)
                    self._regex_f6_pressed = False
            except Exception:
                logger.debug("Regex hotkey release error", exc_info=True)

        self._regex_listener = keyboard.Listener(
            on_press=on_press, on_release=on_release
        )
        self._regex_listener.start()

    def _on_regex_copy(self) -> None:
        entry = self.regex_manager.get_current()
        if entry:
            clipboard = QApplication.clipboard()
            clipboard.setText(entry.pattern)
        self.overlay.show_regex_feedback(entry)

    def _on_regex_next(self) -> None:
        entry = self.regex_manager.next_regex()
        self.overlay.show_regex_feedback(entry)

    def _on_regex_prev(self) -> None:
        entry = self.regex_manager.prev_regex()
        self.overlay.show_regex_feedback(entry)

    def _on_zone_entered(self, zone: str):
        logger.info("_on_zone_entered: zone='%s'", zone)
        self.overlay.handle_zone_enter(zone)
        character = self.config.get("guide.character_name", "")
        if zone.lower() in ["hideout", "your hideout"]:
            if self.config.get("timer.pause_in_hideout", True):
                self.timer.pause()
        else:
            if not self.timer.state.is_running:
                self.timer.start()
            elif self.timer.state.is_paused:
                self.timer.resume()
        if "act" in zone.lower() and character:
            self.timer.advance_act(character)

    def _on_level_up(self, level: int):
        self.overlay.handle_level_up(level)

    def _on_loading(self):
        self.timer.pause()

    def _on_prev_hotkey(self):
        self.overlay._on_prev()

    def _on_next_hotkey(self):
        self.overlay._on_next()

    def _on_scan_gems(self):
        self.overlay.scan_gems()

    def show_settings(self):
        panel = SettingsPanel(self.config, regex_manager=self.regex_manager)
        panel.exec()
        self.overlay.reload_config()

    def run(self):
        return self.app.exec()

    def cleanup(self):
        if hasattr(self, '_focus_timer'):
            self._focus_timer.stop()
        if hasattr(self, '_raise_timer'):
            self._raise_timer.stop()
        if self.watcher:
            self.watcher.stop()
            self.watcher.wait(2000)
        if self.hotkey_listener:
            self.hotkey_listener.stop()
        if hasattr(self, '_regex_listener') and self._regex_listener:
            self._regex_listener.stop()
        self.tracker.cleanup()


def _configure_platform() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "xcb")


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
    _configure_platform()
    app = SinGuideApp()
    try:
        sys.exit(app.run())
    finally:
        app.cleanup()


if __name__ == "__main__":
    main()
