"""Tests for SettingsPanel QDialog — init, config load, signal-driven config.set calls."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from PySide6.QtWidgets import QDialog, QMessageBox

from sin_guide.config.manager import ConfigManager
from sin_guide.core.regex_manager import RegexManager
from sin_guide.overlay.settings_panel import SettingsPanel


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def panel(qtbot, mock_config):
    """Create a SettingsPanel and register it with qtbot."""
    widget = SettingsPanel(mock_config)
    qtbot.addWidget(widget)
    return widget


@pytest.fixture()
def regex_manager(tmp_path: Path):
    with patch("sin_guide.config.manager.Path.home", return_value=tmp_path):
        config = ConfigManager()
    return RegexManager(config)


@pytest.fixture()
def panel_with_regex(qtbot, mock_config, regex_manager):
    widget = SettingsPanel(mock_config, regex_manager=regex_manager)
    qtbot.addWidget(widget)
    return widget


# ---------------------------------------------------------------------------
# Initialisation / visibility
# ---------------------------------------------------------------------------

class TestInit:
    def test_dialog_initialises_without_error(self, qtbot, mock_config) -> None:
        # Arrange / Act
        panel = SettingsPanel(mock_config)
        qtbot.addWidget(panel)

        # Assert — basic attributes exist
        assert panel is not None

    def test_dialog_has_correct_title(self, panel) -> None:
        assert "Settings" in panel.windowTitle()

    def test_dialog_has_minimum_width(self, panel) -> None:
        assert panel.minimumWidth() >= 400

    def test_dialog_can_be_shown(self, qtbot, panel) -> None:
        panel.show()
        qtbot.waitExposed(panel)
        assert panel.isVisible()


# ---------------------------------------------------------------------------
# _load_config populates widgets
# ---------------------------------------------------------------------------

class TestLoadConfig:
    def test_transparency_slider_set_from_config(self, panel, mock_config_values) -> None:
        # Arrange: mock_config_values["overlay.transparency"] = 0.75
        expected = int(mock_config_values["overlay.transparency"] * 100)
        assert panel.transparency_slider.value() == expected

    def test_font_size_slider_set_from_config(self, panel, mock_config_values) -> None:
        expected = mock_config_values["overlay.font_size"]
        assert panel.font_size_slider.value() == expected

    def test_timer_checkbox_set_from_config(self, panel, mock_config_values) -> None:
        expected = mock_config_values["overlay.show_timer"]
        assert panel.timer_check.isChecked() == expected

    def test_character_input_set_from_config(self, panel, mock_config_values) -> None:
        expected = mock_config_values["guide.character_name"]
        assert panel.character_input.text() == expected


# ---------------------------------------------------------------------------
# Slider interactions call config.set
# ---------------------------------------------------------------------------

class TestTransparencySlider:
    def test_moving_slider_calls_config_set(self, qtbot, panel, mock_config) -> None:
        # Arrange
        mock_config.set.reset_mock()

        # Act
        panel.transparency_slider.setValue(80)

        # Assert
        mock_config.set.assert_called_with("overlay.transparency", pytest.approx(0.80))

    def test_transparency_value_is_fraction(self, qtbot, panel, mock_config) -> None:
        mock_config.set.reset_mock()
        panel.transparency_slider.setValue(50)
        mock_config.set.assert_called_with("overlay.transparency", pytest.approx(0.50))


class TestFontSizeSlider:
    def test_moving_slider_calls_config_set(self, qtbot, panel, mock_config) -> None:
        mock_config.set.reset_mock()
        panel.font_size_slider.setValue(18)
        mock_config.set.assert_called_with("overlay.font_size", 18)

    def test_font_size_value_is_integer(self, qtbot, panel, mock_config) -> None:
        mock_config.set.reset_mock()
        panel.font_size_slider.setValue(14)
        args = mock_config.set.call_args
        assert args[0][0] == "overlay.font_size"
        assert isinstance(args[0][1], int)


# ---------------------------------------------------------------------------
# Checkbox interactions call config.set
# ---------------------------------------------------------------------------

class TestTimerCheckbox:
    def test_checking_timer_calls_config_set_true(self, qtbot, panel, mock_config) -> None:
        # Arrange — ensure it starts checked (per mock_config_values)
        panel.timer_check.setChecked(False)
        mock_config.set.reset_mock()

        # Act
        panel.timer_check.setChecked(True)

        # Assert
        mock_config.set.assert_called_with("overlay.show_timer", True)

    def test_unchecking_timer_calls_config_set_false(self, qtbot, panel, mock_config) -> None:
        panel.timer_check.setChecked(True)
        mock_config.set.reset_mock()

        panel.timer_check.setChecked(False)

        mock_config.set.assert_called_with("overlay.show_timer", False)


# ---------------------------------------------------------------------------
# Character name input
# ---------------------------------------------------------------------------

class TestCharacterInput:
    def test_changing_text_calls_config_set(self, qtbot, panel, mock_config) -> None:
        mock_config.set.reset_mock()
        panel.character_input.setText("SinLeague")
        mock_config.set.assert_called_with("guide.character_name", "SinLeague")

    def test_clearing_text_calls_config_set_with_empty(self, qtbot, panel, mock_config) -> None:
        panel.character_input.setText("SomeHero")
        mock_config.set.reset_mock()
        panel.character_input.setText("")
        mock_config.set.assert_called_with("guide.character_name", "")


# ---------------------------------------------------------------------------
# Close button accepts the dialog
# ---------------------------------------------------------------------------

class TestCloseButton:
    def test_close_button_accepts_dialog(self, qtbot, panel) -> None:
        # Arrange
        panel.show()
        qtbot.waitExposed(panel)

        # Act — find the Close button and click it
        from PySide6.QtWidgets import QPushButton
        close_btn = None
        for child in panel.findChildren(QPushButton):
            if child.text() == "Close":
                close_btn = child
                break

        assert close_btn is not None, "Close button not found"

        # Use qtbot to click — dialog.accept() fires, result() becomes Accepted
        with qtbot.waitSignal(panel.accepted, timeout=2000):
            close_btn.click()


# ---------------------------------------------------------------------------
# Regex Storage UI
# ---------------------------------------------------------------------------


class TestRegexUIWithoutManager:
    def test_regex_group_disabled_when_no_manager(self, qtbot, panel) -> None:
        assert panel._regex_group.isEnabled() is False

    def test_add_button_present_but_group_disabled(self, qtbot, panel) -> None:
        # The Add button exists as a widget, but its parent group is disabled.
        assert panel._add_regex_btn is not None
        assert panel._regex_group.isEnabled() is False


class TestRegexUIWithManager:
    def test_regex_group_enabled_with_manager(self, panel_with_regex) -> None:
        assert panel_with_regex._regex_group.isEnabled() is True

    def test_list_is_empty_initially(self, panel_with_regex) -> None:
        assert panel_with_regex._regex_list.count() == 0

    def test_refresh_list_populates_from_manager(self, panel_with_regex) -> None:
        panel_with_regex._regex_manager.add_entry("Maps", "map")
        panel_with_regex._regex_manager.add_entry("Essences", "essence")
        panel_with_regex._refresh_regex_list()

        assert panel_with_regex._regex_list.count() == 2
        assert "Maps" in panel_with_regex._regex_list.item(0).text()
        assert "Essences" in panel_with_regex._regex_list.item(1).text()

    def test_refresh_list_truncates_long_patterns(self, panel_with_regex) -> None:
        long_pattern = "x" * 80
        panel_with_regex._regex_manager.add_entry("Long", long_pattern)
        panel_with_regex._refresh_regex_list()

        text = panel_with_regex._regex_list.item(0).text()
        assert "..." in text
        assert long_pattern[:47] in text

    def test_edit_and_remove_buttons_disabled_when_no_selection(
        self, panel_with_regex,
    ) -> None:
        assert panel_with_regex._edit_regex_btn.isEnabled() is False
        assert panel_with_regex._remove_regex_btn.isEnabled() is False

    def test_edit_and_remove_buttons_enabled_after_selection(
        self, panel_with_regex,
    ) -> None:
        panel_with_regex._regex_manager.add_entry("Maps", "map")
        panel_with_regex._refresh_regex_list()
        panel_with_regex._regex_list.setCurrentRow(0)

        assert panel_with_regex._edit_regex_btn.isEnabled() is True
        assert panel_with_regex._remove_regex_btn.isEnabled() is True

    def test_on_add_regex_calls_manager(self, panel_with_regex, monkeypatch) -> None:
        monkeypatch.setattr(
            SettingsPanel, "_show_regex_dialog",
            lambda self, **_: ("Maps", "map"),
        )
        monkeypatch.setattr(
            "sin_guide.overlay.settings_panel.QMessageBox.warning",
            lambda *a, **kw: None,
        )

        panel_with_regex._on_add_regex()

        assert panel_with_regex._regex_manager.count == 1
        entry = panel_with_regex._regex_manager.list_entries()[0]
        assert entry.name == "Maps"
        assert entry.pattern == "map"

    def test_on_add_regex_bails_when_dialog_cancelled(
        self, panel_with_regex, monkeypatch,
    ) -> None:
        monkeypatch.setattr(
            SettingsPanel, "_show_regex_dialog",
            lambda self, **_: (None, None),
        )

        panel_with_regex._on_add_regex()

        assert panel_with_regex._regex_manager.count == 0

    def test_on_add_regex_shows_warning_on_validation_error(
        self, panel_with_regex, monkeypatch,
    ) -> None:
        monkeypatch.setattr(
            SettingsPanel, "_show_regex_dialog",
            lambda self, **_: ("Maps", ""),
        )

        captured: dict = {}

        def fake_warning(parent, title, text, *args, **kwargs):
            captured["title"] = title
            captured["text"] = text

        monkeypatch.setattr(
            "sin_guide.overlay.settings_panel.QMessageBox.warning",
            fake_warning,
        )

        panel_with_regex._on_add_regex()

        assert panel_with_regex._regex_manager.count == 0
        assert captured.get("title") == "Validation Error"
        assert "non-empty" in captured.get("text", "")

    def test_on_edit_regex_calls_manager(self, panel_with_regex, monkeypatch) -> None:
        panel_with_regex._regex_manager.add_entry("Maps", "map")
        panel_with_regex._refresh_regex_list()
        panel_with_regex._regex_list.setCurrentRow(0)

        monkeypatch.setattr(
            SettingsPanel, "_show_regex_dialog",
            lambda self, **_: ("T16 Maps", "tier 16"),
        )
        monkeypatch.setattr(
            "sin_guide.overlay.settings_panel.QMessageBox.warning",
            lambda *a, **kw: None,
        )

        panel_with_regex._on_edit_regex()

        entry = panel_with_regex._regex_manager.get_entry(0)
        assert entry.name == "T16 Maps"
        assert entry.pattern == "tier 16"

    def test_on_edit_regex_bails_when_no_selection(self, panel_with_regex) -> None:
        panel_with_regex._regex_manager.add_entry("Maps", "map")
        panel_with_regex._refresh_regex_list()
        panel_with_regex._on_edit_regex()
        assert panel_with_regex._regex_manager.get_entry(0).name == "Maps"

    def test_on_edit_regex_bails_when_dialog_cancelled(
        self, panel_with_regex, monkeypatch,
    ) -> None:
        panel_with_regex._regex_manager.add_entry("Maps", "map")
        panel_with_regex._refresh_regex_list()
        panel_with_regex._regex_list.setCurrentRow(0)

        monkeypatch.setattr(
            SettingsPanel, "_show_regex_dialog",
            lambda self, **_: (None, None),
        )

        panel_with_regex._on_edit_regex()

        assert panel_with_regex._regex_manager.get_entry(0).name == "Maps"

    def test_on_remove_regex_calls_manager_when_confirmed(
        self, panel_with_regex, monkeypatch,
    ) -> None:
        panel_with_regex._regex_manager.add_entry("Maps", "map")
        panel_with_regex._regex_manager.add_entry("Essences", "essence")
        panel_with_regex._refresh_regex_list()
        panel_with_regex._regex_list.setCurrentRow(0)

        monkeypatch.setattr(
            "sin_guide.overlay.settings_panel.QMessageBox.question",
            lambda *a, **kw: QMessageBox.StandardButton.Yes,
        )

        panel_with_regex._on_remove_regex()

        assert panel_with_regex._regex_manager.count == 1
        assert panel_with_regex._regex_manager.get_entry(0).name == "Essences"

    def test_on_remove_regex_skips_when_user_declines(
        self, panel_with_regex, monkeypatch,
    ) -> None:
        panel_with_regex._regex_manager.add_entry("Maps", "map")
        panel_with_regex._refresh_regex_list()
        panel_with_regex._regex_list.setCurrentRow(0)

        monkeypatch.setattr(
            "sin_guide.overlay.settings_panel.QMessageBox.question",
            lambda *a, **kw: QMessageBox.StandardButton.No,
        )

        panel_with_regex._on_remove_regex()

        assert panel_with_regex._regex_manager.count == 1

    def test_on_remove_regex_bails_when_no_selection(self, panel_with_regex) -> None:
        panel_with_regex._regex_manager.add_entry("Maps", "map")
        panel_with_regex._refresh_regex_list()
        panel_with_regex._on_remove_regex()
        assert panel_with_regex._regex_manager.count == 1

    def test_no_op_when_no_manager(self, qtbot, mock_config) -> None:
        panel = SettingsPanel(mock_config)
        qtbot.addWidget(panel)

        panel._on_add_regex()
        panel._on_edit_regex()
        panel._on_remove_regex()
        panel._refresh_regex_list()
        assert panel._regex_list.count() == 0


class TestShowRegexDialog:
    def test_show_regex_dialog_returns_inputs_on_accept(
        self, panel_with_regex, monkeypatch,
    ) -> None:
        monkeypatch.setattr(
            "sin_guide.overlay.settings_panel.QDialog.exec",
            lambda self: QDialog.DialogCode.Accepted,
        )

        name, pattern = panel_with_regex._show_regex_dialog(
            title="Add Regex", name="Maps", pattern="map"
        )

        assert name == "Maps"
        assert pattern == "map"

    def test_show_regex_dialog_returns_none_on_cancel(
        self, panel_with_regex, monkeypatch,
    ) -> None:
        monkeypatch.setattr(
            "sin_guide.overlay.settings_panel.QDialog.exec",
            lambda self: QDialog.DialogCode.Rejected,
        )

        name, pattern = panel_with_regex._show_regex_dialog(title="Add Regex")

        assert name is None
        assert pattern is None
