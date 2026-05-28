"""Tests for overlay resize functionality — ResizeHandle, width constraints, persistence."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QSizePolicy

from sin_guide.overlay.main_window import ResizeHandle


class TestResizeHandleWidget:
    def test_resize_handle_exists(self, make_overlay):
        overlay = make_overlay(steps=[])
        assert hasattr(overlay, "resize_handle")
        assert isinstance(overlay.resize_handle, ResizeHandle)

    def test_resize_handle_cursor(self, make_overlay):
        overlay = make_overlay(steps=[])
        assert overlay.resize_handle.cursor().shape() == Qt.CursorShape.SizeFDiagCursor

    def test_resize_handle_tooltip(self, make_overlay):
        overlay = make_overlay(steps=[])
        assert overlay.resize_handle.toolTip() == "Drag to resize overlay"

    def test_resize_handle_target_set(self, make_overlay):
        overlay = make_overlay(steps=[])
        assert overlay.resize_handle._target is overlay

    def test_resize_handle_fixed_size(self, make_overlay):
        overlay = make_overlay(steps=[])
        assert overlay.resize_handle.width() == 14
        assert overlay.resize_handle.height() == 14

    def test_resize_handle_style_consistent_with_drag_handle(self, make_overlay):
        overlay = make_overlay(steps=[])
        rh_ss = overlay.resize_handle.styleSheet()
        dh_ss = overlay.drag_handle.styleSheet()
        for color in ("rgba(0, 220, 220, 120)", "rgba(0, 255, 255, 180)"):
            assert color in rh_ss
            assert color in dh_ss
        assert "border-radius: 3px" in rh_ss
        assert "border-radius: 3px" in dh_ss


class TestOverlayWidthConstraints:
    def test_minimum_width_enforced(self, make_overlay, mock_config_values):
        mock_config_values["overlay.width"] = 100
        overlay = make_overlay(steps=[])
        assert overlay.width() >= 180

    def test_maximum_width_enforced(self, make_overlay, mock_config_values):
        mock_config_values["overlay.width"] = 1000
        overlay = make_overlay(steps=[])
        assert overlay.width() <= 600

    def test_setMinimumWidth_called(self, make_overlay):
        overlay = make_overlay(steps=[])
        assert overlay.minimumWidth() == 180

    def test_setMaximumWidth_called(self, make_overlay):
        overlay = make_overlay(steps=[])
        assert overlay.maximumWidth() == 600

    def test_normal_width_unchanged(self, make_overlay):
        overlay = make_overlay(steps=[])
        assert overlay.width() == 220

    def test_width_config_applied(self, make_overlay, mock_config_values):
        mock_config_values["overlay.width"] = 300
        overlay = make_overlay(steps=[])
        assert overlay.width() == 300


class TestResizePersistence:
    def test_resize_saves_new_width_to_config(self, make_overlay):
        overlay = make_overlay(steps=[])
        old_width = overlay.width()
        new_width = old_width + 50
        overlay.config.set.reset_mock()
        overlay.resize(new_width, overlay.height())
        overlay.config.set.assert_called_with("overlay.width", new_width)

    def test_resize_skips_save_when_width_unchanged(self, make_overlay):
        overlay = make_overlay(steps=[])
        overlay.config.set.reset_mock()
        overlay.resize(overlay.width(), overlay.height())
        same_calls = [c for c in overlay.config.set.call_args_list if c[0][0] == "overlay.width"]
        assert len(same_calls) == 0

    def test_reload_config_preserves_enforced_bounds(self, make_overlay, mock_config):
        overlay = make_overlay(steps=[])
        overlay.resize(100, overlay.height())
        assert overlay.width() >= 180


class TestHeightAutoSized:
    def test_height_stays_content_driven(self, make_overlay, mock_config):
        overlay = make_overlay(steps=[])
        bare_height = overlay.height()
        from tests.conftest import make_step
        overlay = make_overlay(steps=[make_step(description="Line 1"), make_step(description="Line 2")])
        assert overlay.height() != bare_height

    def test_resize_does_not_affect_height_policy(self, make_overlay):
        overlay = make_overlay(steps=[])
        policy = overlay.sizePolicy()
        assert policy.verticalPolicy() == QSizePolicy.Policy.Minimum


class TestSizePolicy:
    def test_horizontal_policy_allows_resize(self, make_overlay):
        overlay = make_overlay(steps=[])
        policy = overlay.sizePolicy()
        assert policy.horizontalPolicy() != QSizePolicy.Policy.Fixed
