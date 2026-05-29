import json
import logging
from pathlib import Path

from PySide6.QtCore import Qt, QPoint, QTimer
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QSizePolicy,
)

from sin_guide.overlay.gem_widget import GemWidget
from sin_guide.overlay.step_renderer import render_steps
from sin_guide.data.zone_rewards import ZONE_LEAGUE_REWARDS

logger = logging.getLogger(__name__)

_ZONE_LEVELS: dict[str, int] | None = None


def _load_zone_levels() -> dict[str, int]:
    global _ZONE_LEVELS
    if _ZONE_LEVELS is None:
        _data_path = Path(__file__).parent.parent / "data" / "zones.json"
        with open(_data_path) as f:
            _ZONE_LEVELS = json.load(f)
    return _ZONE_LEVELS


class DragHandle(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._drag_pos: QPoint | None = None
        self._target: QWidget | None = None
        self.setFixedSize(14, 14)
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.setStyleSheet("""
            DragHandle {
                background-color: rgba(0, 220, 220, 120);
                border: 1px solid rgba(0, 255, 255, 180);
                border-radius: 3px;
            }
            DragHandle:hover {
                background-color: rgba(0, 255, 255, 200);
            }
        """)
        self.setToolTip("Drag to move overlay")

    def set_target(self, target: QWidget):
        self._target = target

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton and self._target:
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            handle = self._target.windowHandle()
            if handle:
                handle.startSystemMove()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        pass

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._drag_pos = None
        self.setCursor(Qt.CursorShape.OpenHandCursor)


class ResizeHandle(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._target: QWidget | None = None
        self.setFixedSize(14, 14)
        self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        self.setStyleSheet("""
            ResizeHandle {
                background-color: rgba(0, 220, 220, 120);
                border: 1px solid rgba(0, 255, 255, 180);
                border-radius: 3px;
            }
            ResizeHandle:hover {
                background-color: rgba(0, 255, 255, 200);
            }
        """)
        self.setToolTip("Drag to resize overlay width")

    def set_target(self, target: QWidget):
        self._target = target

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton and self._target:
            handle = self._target.windowHandle()
            if handle:
                handle.startSystemResize(
                    Qt.Edge.RightEdge | Qt.Edge.BottomEdge
                )
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        pass

    def mouseReleaseEvent(self, event: QMouseEvent):
        pass


class OverlayWindow(QWidget):
    def __init__(self, config_manager, guide_engine, timer, exp_calc):
        super().__init__()
        self.config = config_manager
        self.guide = guide_engine
        self.timer = timer
        self.exp_calc = exp_calc
        self._player_level: int | None = None
        self._gem_db: dict = {}
        self._gem_widget: GemWidget | None = None
        self._pending_width: int | None = None
        self._setup_ui()
        self._apply_config()
        self._start_refresh()

    def _setup_ui(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)

        self.main_frame = QFrame(self)
        self.main_frame.setObjectName("mainFrame")
        self.main_frame.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)

        layout = QVBoxLayout(self.main_frame)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(2)

        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(4)

        self.header_label = QLabel("Act 1")
        self.header_label.setObjectName("headerLabel")
        top_row.addWidget(self.header_label)
        top_row.addStretch()

        self.drag_handle = DragHandle(self.main_frame)
        self.drag_handle.set_target(self)
        top_row.addWidget(self.drag_handle, alignment=Qt.AlignmentFlag.AlignTop)

        self.settings_btn = QPushButton("⚙")
        self.settings_btn.setObjectName("settingsButton")
        self.settings_btn.setFixedSize(18, 18)
        self.settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.settings_btn.setToolTip("Settings")
        self.settings_btn.clicked.connect(self._open_settings_dialog)
        top_row.addWidget(self.settings_btn, alignment=Qt.AlignmentFlag.AlignTop)

        self.import_btn = QPushButton("📦")
        self.import_btn.setObjectName("importButton")
        self.import_btn.setFixedSize(18, 18)
        self.import_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.import_btn.setToolTip("Import PoB Build")
        self.import_btn.clicked.connect(self._import_pob)
        top_row.addWidget(self.import_btn, alignment=Qt.AlignmentFlag.AlignTop)

        layout.addLayout(top_row)

        self.steps_container = QVBoxLayout()
        self.steps_container.setSpacing(1)
        self.steps_container.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(self.steps_container)

        self._gem_placeholder = QWidget()
        self._gem_placeholder.setVisible(False)
        layout.addWidget(self._gem_placeholder)

        self.timer_label = QLabel("0:00 | A1 | 0:00")
        self.timer_label.setObjectName("timerLabel")
        layout.addWidget(self.timer_label)

        self.exp_label = QLabel("")
        self.exp_label.setObjectName("expLabel")
        layout.addWidget(self.exp_label)

        nav_layout = QHBoxLayout()
        self.prev_btn = QPushButton("<")
        self.prev_btn.setObjectName("navButton")
        self.prev_btn.setFixedSize(40, 30)
        self.prev_btn.clicked.connect(self._on_prev)
        nav_layout.addWidget(self.prev_btn)

        nav_layout.addStretch()

        self.next_btn = QPushButton(">")
        self.next_btn.setObjectName("navButton")
        self.next_btn.setFixedSize(40, 30)
        self.next_btn.clicked.connect(self._on_next)
        nav_layout.addWidget(self.next_btn)

        self.resize_handle = ResizeHandle(self.main_frame)
        self.resize_handle.set_target(self)
        nav_layout.addWidget(self.resize_handle, alignment=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom)

        layout.addLayout(nav_layout)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.main_frame)
        self.setLayout(main_layout)

    def _apply_config(self):
        transparency = self.config.get("overlay.transparency", 0.75)
        font_size = self.config.get("overlay.font_size", 14)
        width = self.config.get("overlay.width", 400)
        x = self.config.get("overlay.x", 100)
        y = self.config.get("overlay.y", 100)
        show_timer = self.config.get("overlay.show_timer", True)
        show_exp = self.config.get("overlay.show_effective_exp", True)

        alpha = int(255 * transparency)
        self.main_frame.setStyleSheet(f"""
            QFrame#mainFrame {{
                background-color: rgba(0, 0, 0, {alpha});
                border: 1px solid rgba(255, 255, 255, 30);
                border-radius: 4px;
            }}
            QLabel {{
                color: white;
                font-size: {font_size - 1}px;
                font-family: 'Segoe UI', 'Ubuntu', sans-serif;
                padding: 0px;
                margin: 0px;
            }}
            QLabel#headerLabel {{
                font-weight: bold;
                font-size: {font_size}px;
                border-bottom: 1px solid rgba(255, 255, 255, 50);
                padding-bottom: 2px;
                margin-bottom: 1px;
            }}
            QLabel#timerLabel {{
                color: #aaaaaa;
                font-size: {font_size - 3}px;
                border-top: 1px solid rgba(255, 255, 255, 30);
                padding-top: 2px;
                margin-top: 1px;
            }}
            QLabel#expLabel {{
                color: #00ff00;
                font-size: {font_size - 3}px;
                padding-top: 1px;
            }}
            QPushButton#navButton {{
                background-color: rgba(255, 255, 255, 40);
                color: white;
                border: none;
                border-radius: 3px;
                font-size: {font_size - 1}px;
                font-weight: bold;
                padding: 2px;
                min-height: 20px;
                max-height: 24px;
            }}
            QPushButton#navButton:hover {{
                background-color: rgba(255, 255, 255, 60);
            }}
            QPushButton#settingsButton {{
                background-color: transparent;
                color: rgba(255, 255, 255, 100);
                border: none;
                font-size: {font_size - 2}px;
                padding: 0px;
            }}
            QPushButton#settingsButton:hover {{
                color: white;
                background-color: rgba(255, 255, 255, 30);
                border-radius: 2px;
            }}
            QPushButton#importButton {{
                background-color: transparent;
                color: rgba(255, 255, 255, 100);
                border: none;
                font-size: {font_size - 2}px;
                padding: 0px;
            }}
            QPushButton#importButton:hover {{
                color: white;
                background-color: rgba(255, 255, 255, 30);
                border-radius: 2px;
            }}
            QLabel#gemsHeader {{
                color: #888888;
                font-size: 10px;
                font-weight: bold;
                margin-top: 2px;
            }}
        """)

        self.setMinimumWidth(180)
        self.setMaximumWidth(600)
        self.resize(width, self.height())
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)

        screen = QApplication.primaryScreen()
        if x < 0 or y < 0 or not self._is_on_screen(x, y, screen):
            logger.debug(f"Saved position ({x},{y}) is off-screen — resetting to bottom-centre")
            self._position_bottom_center()
        else:
            self.move(x, y)

        self.timer_label.setVisible(show_timer)
        self.exp_label.setVisible(show_exp)

    def _is_on_screen(self, x: int, y: int, screen) -> bool:
        if not screen:
            return False
        geo = screen.availableGeometry()
        # Require at least the top-left corner to be within the screen
        return geo.x() <= x < geo.x() + geo.width() and geo.y() <= y < geo.y() + geo.height()

    def _position_bottom_center(self):
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            x = (geo.width() - self.width()) // 2
            y = geo.height() - 200
            self.move(x, y)
            self.config.set("overlay.x", x)
            self.config.set("overlay.y", y)

    def _start_refresh(self):
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self._update_display)
        self.refresh_timer.timeout.connect(self.raise_)
        self.refresh_timer.start(1000)
        self._update_display()

    def _update_display(self):
        league_start = self.config.get("guide.league_start", True)
        show_optionals = self.config.get("guide.show_optionals", True)
        max_lines = self.config.get("overlay.max_visible_lines", 5)
        show_timer = self.config.get("overlay.show_timer", True)
        show_exp = self.config.get("overlay.show_effective_exp", True)
        character = self.config.get("guide.character_name", "")

        steps = self.guide.get_visible_steps(league_start, show_optionals, max_lines)

        current_zone = render_steps(self.steps_container, steps, self.width(), ZONE_LEAGUE_REWARDS)

        if steps:
            self.header_label.setText(f"Act {steps[0].act}")

        self._render_gems()

        if show_timer:
            self.timer_label.setText(self.timer.get_display())
        else:
            self.timer_label.setText("")

        if show_exp and character:
            zone_level = self._estimate_zone_level(current_zone)
            player_level = self._get_player_level()
            if zone_level and player_level:
                self.exp_label.setText(self.exp_calc.display(player_level, zone_level))
            else:
                self.exp_label.setText("")
        else:
            self.exp_label.setText("")

        self.adjustSize()

    def _estimate_zone_level(self, zone: str) -> int | None:
        return _load_zone_levels().get(zone)

    def _get_player_level(self) -> int | None:
        return self._player_level

    def _on_prev(self):
        self.guide.retreat()
        self._update_display()

    def _on_next(self):
        self.guide.advance()
        self._update_display()

    def _open_settings_dialog(self):
        if hasattr(self, 'on_settings_requested') and self.on_settings_requested:
            self.on_settings_requested()

    def _render_gems(self):
        if self._gem_widget is not None:
            self._gem_widget.set_player_level(self._player_level)

    def moveEvent(self, event):
        super().moveEvent(event)
        self.config.set("overlay.x", self.x())
        self.config.set("overlay.y", self.y())

    def resizeEvent(self, event):
        super().resizeEvent(event)
        new_width = event.size().width()
        old_width = event.oldSize().width()
        if new_width != old_width:
            self._pending_width = new_width
            QTimer.singleShot(300, self._flush_pending_width)

    def _flush_pending_width(self):
        if self._pending_width is not None:
            self.config.set("overlay.width", self._pending_width)
            self._pending_width = None

    def show_overlay(self):
        self.show()
        self.raise_()

    def hide_overlay(self):
        self.hide()

    def handle_zone_enter(self, zone: str):
        logger.debug(f"handle_zone_enter('{zone}') — current_step_id={self.guide.current_step_id}, current_zone={self.guide.current_zone}")
        self.guide.handle_zone_enter(zone)
        self._update_display()

    def handle_level_up(self, level: int):
        if self._player_level is None or level > self._player_level:
            self._player_level = level

    def reload_config(self):
        self.config.reload()
        self._apply_config()
        self._update_display()

    def _import_pob(self):
        from PySide6.QtWidgets import QInputDialog

        url, ok = QInputDialog.getText(self, "Import PoB Build", "pobb.in URL:")
        if not ok or not url.strip():
            return
        try:
            self._ensure_gem_widget()
            if self._gem_widget.import_build(url.strip()):
                self._update_display()
        except Exception as e:
            logger.error("PoB import failed: %s", e, exc_info=True)

    def scan_gems(self):
        self._ensure_gem_widget()
        screen = self.screen()
        if not screen:
            return
        try:
            pixmap = screen.grabWindow(0)
            img = pixmap.toImage()
            from PIL import Image
            import io
            buf = io.BytesIO()
            img.save(buf, "PNG")
            buf.seek(0)
            pil_img = Image.open(buf)
            self._gem_widget.scan_gems(pil_img)
        except Exception as e:
            logger.error("Gem scan failed: %s", e, exc_info=True)
        self._update_display()

    def _ensure_gem_widget(self):
        """Lazily create and insert GemWidget into the layout."""
        if self._gem_widget is not None:
            return
        from sin_guide.core.gem_cutter import load_gem_db
        self._gem_db = load_gem_db()
        self._gem_widget = GemWidget(self._gem_db)
        layout = self.main_frame.layout()
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item and item.widget() is self._gem_placeholder:
                layout.insertWidget(i, self._gem_widget)
                self._gem_widget.show()
                self._gem_placeholder.hide()
                break
