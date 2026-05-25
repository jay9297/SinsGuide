from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QSlider,
    QLineEdit,
    QCheckBox,
    QPushButton,
    QGroupBox,
    QFormLayout,
    QFileDialog,
)


class SettingsPanel(QDialog):
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config = config_manager
        self.setWindowTitle("Sin's Guide - Settings")
        self.setMinimumWidth(400)
        self._setup_ui()
        self._load_config()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        overlay_group = QGroupBox("Overlay")
        overlay_layout = QFormLayout()

        self.transparency_slider = QSlider(Qt.Orientation.Horizontal)
        self.transparency_slider.setRange(10, 100)
        self.transparency_slider.setTickInterval(10)
        self.transparency_slider.valueChanged.connect(self._on_transparency_changed)
        overlay_layout.addRow("Transparency:", self.transparency_slider)

        self.font_size_slider = QSlider(Qt.Orientation.Horizontal)
        self.font_size_slider.setRange(10, 24)
        self.font_size_slider.setTickInterval(2)
        self.font_size_slider.valueChanged.connect(self._on_font_size_changed)
        overlay_layout.addRow("Font Size:", self.font_size_slider)

        self.timer_check = QCheckBox("Show Timer")
        self.timer_check.stateChanged.connect(self._on_timer_changed)
        overlay_layout.addRow(self.timer_check)

        self.exp_check = QCheckBox("Show Effective EXP")
        self.exp_check.stateChanged.connect(self._on_exp_changed)
        overlay_layout.addRow(self.exp_check)

        overlay_group.setLayout(overlay_layout)
        layout.addWidget(overlay_group)

        guide_group = QGroupBox("Guide")
        guide_layout = QFormLayout()

        self.league_start_check = QCheckBox("League Start Mode")
        self.league_start_check.stateChanged.connect(self._on_league_start_changed)
        guide_layout.addRow(self.league_start_check)

        self.optionals_check = QCheckBox("Show Optional Steps")
        self.optionals_check.stateChanged.connect(self._on_optionals_changed)
        guide_layout.addRow(self.optionals_check)

        self.character_input = QLineEdit()
        self.character_input.textChanged.connect(self._on_character_changed)
        guide_layout.addRow("Character Name:", self.character_input)

        guide_group.setLayout(guide_layout)
        layout.addWidget(guide_group)

        hotkeys_group = QGroupBox("Hotkeys")
        hotkeys_layout = QFormLayout()

        self.prev_hotkey = QLineEdit()
        self.prev_hotkey.setMaxLength(10)
        self.prev_hotkey.textChanged.connect(self._on_prev_hotkey_changed)
        hotkeys_layout.addRow("Previous Step:", self.prev_hotkey)

        self.next_hotkey = QLineEdit()
        self.next_hotkey.setMaxLength(10)
        self.next_hotkey.textChanged.connect(self._on_next_hotkey_changed)
        hotkeys_layout.addRow("Next Step:", self.next_hotkey)

        hotkeys_group.setLayout(hotkeys_layout)
        layout.addWidget(hotkeys_group)

        paths_group = QGroupBox("Paths")
        paths_layout = QHBoxLayout()

        self.client_txt_input = QLineEdit()
        self.client_txt_input.setReadOnly(True)
        paths_layout.addWidget(self.client_txt_input)

        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._on_browse_client_txt)
        paths_layout.addWidget(browse_btn)

        paths_group.setLayout(paths_layout)
        layout.addWidget(paths_group)

        layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

    def _load_config(self):
        self.transparency_slider.setValue(int(self.config.get("overlay.transparency", 0.75) * 100))
        self.font_size_slider.setValue(self.config.get("overlay.font_size", 14))
        self.timer_check.setChecked(self.config.get("overlay.show_timer", True))
        self.exp_check.setChecked(self.config.get("overlay.show_effective_exp", True))
        self.league_start_check.setChecked(self.config.get("guide.league_start", True))
        self.optionals_check.setChecked(self.config.get("guide.show_optionals", True))
        self.character_input.setText(self.config.get("guide.character_name", ""))
        self.prev_hotkey.setText(self.config.get("hotkeys.prev_step", "F3"))
        self.next_hotkey.setText(self.config.get("hotkeys.next_step", "F4"))
        self.client_txt_input.setText(self.config.get("paths.client_txt", ""))

    def _on_transparency_changed(self, value: int):
        self.config.set("overlay.transparency", value / 100)

    def _on_font_size_changed(self, value: int):
        self.config.set("overlay.font_size", value)

    def _on_timer_changed(self, state: int):
        self.config.set("overlay.show_timer", state == Qt.CheckState.Checked.value)

    def _on_exp_changed(self, state: int):
        self.config.set("overlay.show_effective_exp", state == Qt.CheckState.Checked.value)

    def _on_league_start_changed(self, state: int):
        self.config.set("guide.league_start", state == Qt.CheckState.Checked.value)

    def _on_optionals_changed(self, state: int):
        self.config.set("guide.show_optionals", state == Qt.CheckState.Checked.value)

    def _on_character_changed(self, text: str):
        self.config.set("guide.character_name", text)

    def _on_prev_hotkey_changed(self, text: str):
        self.config.set("hotkeys.prev_step", text)

    def _on_next_hotkey_changed(self, text: str):
        self.config.set("hotkeys.next_step", text)

    def _on_browse_client_txt(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Client.txt", "", "Text Files (*.txt)"
        )
        if path:
            self.client_txt_input.setText(path)
            self.config.set("paths.client_txt", path)
