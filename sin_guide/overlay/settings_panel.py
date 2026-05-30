from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPushButton,
    QSlider,
    QCheckBox,
    QVBoxLayout,
)

from sin_guide.core.regex_manager import RegexValidationError

if TYPE_CHECKING:
    from sin_guide.core.regex_manager import RegexManager


class SettingsPanel(QDialog):
    def __init__(self, config_manager, parent=None, *, regex_manager: RegexManager | None = None):
        super().__init__(parent)
        self.config = config_manager
        self._regex_manager = regex_manager
        self.setWindowTitle("Sin's Guide - Settings")
        self.setMinimumWidth(400)
        self._setup_ui()
        self._load_config()
        if regex_manager is not None:
            self._refresh_regex_list()

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

        self._setup_regex_ui(layout)

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

    # ------------------------------------------------------------------
    # Regex Storage
    # ------------------------------------------------------------------

    def _setup_regex_ui(self, layout: QVBoxLayout) -> None:
        self._regex_group = QGroupBox("Regex Storage")
        regex_layout = QVBoxLayout()

        self._regex_list = QListWidget()
        self._regex_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        regex_layout.addWidget(self._regex_list)

        btn_layout = QHBoxLayout()

        self._add_regex_btn = QPushButton("Add")
        self._add_regex_btn.clicked.connect(self._on_add_regex)
        btn_layout.addWidget(self._add_regex_btn)

        self._edit_regex_btn = QPushButton("Edit")
        self._edit_regex_btn.clicked.connect(self._on_edit_regex)
        btn_layout.addWidget(self._edit_regex_btn)

        self._remove_regex_btn = QPushButton("Remove")
        self._remove_regex_btn.clicked.connect(self._on_remove_regex)
        btn_layout.addWidget(self._remove_regex_btn)

        regex_layout.addLayout(btn_layout)
        self._regex_group.setLayout(regex_layout)
        layout.addWidget(self._regex_group)

        self._update_regex_buttons()

    def _refresh_regex_list(self) -> None:
        self._regex_list.clear()
        if self._regex_manager is None:
            return

        for entry in self._regex_manager.list_entries():
            pattern_preview = (
                entry.pattern[:47] + "..."
                if len(entry.pattern) > 50
                else entry.pattern
            )
            display = f"{entry.name}  [{pattern_preview}]"
            self._regex_list.addItem(display)

    def _update_regex_buttons(self) -> None:
        has_manager = self._regex_manager is not None

        self._regex_group.setEnabled(has_manager)
        if not has_manager:
            return

        has_selection = self._regex_list.currentRow() >= 0

        self._add_regex_btn.setEnabled(True)
        self._edit_regex_btn.setEnabled(has_selection)
        self._remove_regex_btn.setEnabled(has_selection)

    def _on_add_regex(self) -> None:
        if self._regex_manager is None:
            return
        name, pattern = self._show_regex_dialog(title="Add Regex")
        if name is None or pattern is None:
            return

        try:
            self._regex_manager.add_entry(name, pattern)
            self._refresh_regex_list()
        except RegexValidationError as e:
            QMessageBox.warning(self, "Validation Error", str(e))

    def _on_edit_regex(self) -> None:
        if self._regex_manager is None:
            return
        row = self._regex_list.currentRow()
        if row < 0:
            return

        entry = self._regex_manager.get_entry(row)
        name, pattern = self._show_regex_dialog(
            title="Edit Regex", name=entry.name, pattern=entry.pattern
        )
        if name is None or pattern is None:
            return

        try:
            self._regex_manager.update_entry(row, name, pattern)
            self._refresh_regex_list()
        except RegexValidationError as e:
            QMessageBox.warning(self, "Validation Error", str(e))

    def _on_remove_regex(self) -> None:
        if self._regex_manager is None:
            return
        row = self._regex_list.currentRow()
        if row < 0:
            return

        entry = self._regex_manager.get_entry(row)
        reply = QMessageBox.question(
            self,
            "Confirm Removal",
            f'Remove regex entry "{entry.name}"?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        self._regex_manager.remove_entry(row)
        self._refresh_regex_list()

    def _show_regex_dialog(
        self,
        title: str,
        name: str = "",
        pattern: str = "",
    ) -> tuple[str | None, str | None]:
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.setMinimumWidth(380)
        dialog_layout = QVBoxLayout(dialog)

        name_layout = QFormLayout()
        name_input = QLineEdit()
        name_input.setText(name)
        name_input.setMaxLength(50)
        name_layout.addRow("Name:", name_input)
        dialog_layout.addLayout(name_layout)

        pattern_layout = QFormLayout()
        pattern_input = QLineEdit()
        pattern_input.setText(pattern)
        pattern_input.setMaxLength(250)
        pattern_layout.addRow("Pattern:", pattern_input)
        dialog_layout.addLayout(pattern_layout)

        hint_label = QLabel()
        hint_label.setStyleSheet("color: #888;")
        dialog_layout.addWidget(hint_label)

        name_input.textChanged.connect(
            lambda t: hint_label.setText(
                f"Name: {len(t)}/50 chars, Pattern: {len(pattern_input.text())}/250 chars"
            )
        )
        pattern_input.textChanged.connect(
            lambda t: hint_label.setText(
                f"Name: {len(name_input.text())}/50 chars, Pattern: {len(t)}/250 chars"
            )
        )

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        dialog_layout.addWidget(buttons)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return None, None

        return name_input.text(), pattern_input.text()
