"""Tests for SettingsPanel QDialog — init, config load, signal-driven config.set calls."""
from __future__ import annotations

import pytest

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
