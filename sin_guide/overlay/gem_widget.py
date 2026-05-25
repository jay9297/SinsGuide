from __future__ import annotations


from PIL import Image
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget

from sin_guide.core.gem_cutter import GemCutter
from sin_guide.core.gem_ocr import GemOCR
from sin_guide.utils.pob_parser import GemSetup, PoBParser


class GemWidget(QWidget):
    """Shows gem availability from imported PoB build and OCR scan."""

    def __init__(self, gem_db: dict, parent: QWidget | None = None):
        super().__init__(parent)
        self._cutter = GemCutter(gem_db)
        self._build_gems: list[GemSetup] = []
        self._player_level: int | None = None
        self._scan_result: dict | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._separator = QFrame()
        self._separator.setFrameShape(QFrame.Shape.HLine)
        self._separator.setStyleSheet("color: rgba(255, 255, 255, 30);")
        self._separator.setVisible(False)
        layout.addWidget(self._separator)

        self._header = QLabel("Gems")
        self._header.setObjectName("gemsHeader")
        self._header.setVisible(False)
        layout.addWidget(self._header)

        self._content_layout = QVBoxLayout()
        self._content_layout.setSpacing(0)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(self._content_layout)

    @property
    def has_content(self) -> bool:
        return bool(self._build_gems)

    def set_build(self, gems: list[GemSetup]) -> None:
        self._build_gems = gems
        self._scan_result = None
        self._render()

    def set_player_level(self, level: int | None) -> None:
        self._player_level = level
        if self._build_gems:
            self._render()

    def set_scan_result(self, result: dict | None) -> None:
        self._scan_result = result
        self._render()

    def import_build(self, url: str) -> bool:
        parser = PoBParser()
        build = parser.parse_url(url)
        if not build:
            return False
        self._build_gems = build.gems
        self._scan_result = None
        self._render()
        return True

    def scan_gems(self, screenshot: Image.Image) -> None:
        ocr = GemOCR()
        names = ocr.extract_names_from_image(screenshot)
        if names and self._build_gems:
            needed = self._cutter.get_available_from_vendor(names, self._build_gems)
            self._scan_result = {"available": names, "needed": needed}
        else:
            self._scan_result = None
        self._render()

    def _render(self) -> None:
        while self._content_layout.count():
            child = self._content_layout.takeAt(0)
            if child is not None and child.widget() is not None:
                child.widget().deleteLater()

        visible = bool(self._build_gems)
        self._separator.setVisible(visible)
        self._header.setVisible(visible)

        if not visible:
            return

        if self._scan_result:
            self._render_scan_result()
        elif self._player_level is not None:
            self._render_level_gems()
        else:
            self._render_prompt()

    def _render_scan_result(self) -> None:
        assert self._scan_result is not None
        needed = set(n.lower() for n in self._scan_result.get("needed", []))
        available = self._scan_result.get("available", [])

        by_type: dict[str, list[tuple[str, bool]]] = {}
        for name in available:
            info = self._cutter._db.get(name.lower())
            if info is None:
                continue
            t = info["type"]
            by_type.setdefault(t, []).append((name, name.lower() in needed))

        for t in by_type:
            by_type[t].sort(key=lambda x: x[0])

        type_order = ["skill", "spirit", "support"]
        type_labels = {"skill": "Skill Gems", "spirit": "Spirit Gems", "support": "Support Gems"}

        first = True
        for gem_type in type_order:
            if gem_type not in by_type:
                continue

            if not first:
                sep = QFrame()
                sep.setFrameShape(QFrame.Shape.HLine)
                sep.setStyleSheet("color: rgba(255, 255, 255, 30);")
                self._content_layout.addWidget(sep)
            first = False

            header = QLabel(type_labels[gem_type])
            header.setStyleSheet("color: #888888; font-size: 10px; font-weight: bold;")
            self._content_layout.addWidget(header)

            for name, is_needed in by_type[gem_type]:
                label = QLabel()
                if is_needed:
                    label.setText(f"  ✓ {name}")
                    label.setStyleSheet("color: #00ff00; font-size: 10px;")
                else:
                    label.setText(f"  ✗ {name}")
                    label.setStyleSheet("color: #ff4444; font-size: 10px;")
                self._content_layout.addWidget(label)

    def _render_level_gems(self) -> None:
        assert self._player_level is not None
        available = self._cutter.get_available_gems(self._player_level, self._build_gems)
        upcoming = self._cutter.get_upcoming_gems(self._player_level, self._build_gems, horizon=3)

        if not available and not upcoming:
            self._render_prompt()
            return

        by_type: dict[str, dict[str, list[dict]]] = {}
        for g in available:
            t = g["type"]
            by_type.setdefault(t, {"available": [], "upcoming": []})
            by_type[t]["available"].append(g)
        for g in upcoming:
            t = g["type"]
            by_type.setdefault(t, {"available": [], "upcoming": []})
            by_type[t]["upcoming"].append(g)

        for t in by_type:
            by_type[t]["available"].sort(key=lambda g: g["name"])
            by_type[t]["upcoming"].sort(key=lambda g: g["name"])

        type_order = ["skill", "spirit", "support"]
        type_labels = {"skill": "Skill Gems", "spirit": "Spirit Gems", "support": "Support Gems"}

        first = True
        for gem_type in type_order:
            if gem_type not in by_type:
                continue

            if not first:
                sep = QFrame()
                sep.setFrameShape(QFrame.Shape.HLine)
                sep.setStyleSheet("color: rgba(255, 255, 255, 30);")
                self._content_layout.addWidget(sep)
            first = False

            header = QLabel(type_labels[gem_type])
            header.setStyleSheet("color: #888888; font-size: 10px; font-weight: bold;")
            self._content_layout.addWidget(header)

            for g in by_type[gem_type]["available"]:
                if g.get("unknown"):
                    label = QLabel(f"  ? {g['name']}")
                    label.setStyleSheet("color: #888888; font-size: 10px;")
                else:
                    label = QLabel(f"  ✓ {g['name']}")
                    label.setStyleSheet("color: #00ff00; font-size: 10px;")
                self._content_layout.addWidget(label)

            for g in by_type[gem_type]["upcoming"]:
                label = QLabel(f"  ~ {g['name']} (L{g['level_required']}, in {g['levels_away']})")
                label.setStyleSheet("color: #aaaa00; font-size: 10px;")
                self._content_layout.addWidget(label)

    def _render_prompt(self) -> None:
        label = QLabel("  Import build, then scan gems (F5)")
        label.setStyleSheet("color: #888888; font-size: 10px;")
        self._content_layout.addWidget(label)
