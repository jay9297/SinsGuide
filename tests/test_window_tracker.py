"""Tests for WindowTracker — Xlib mocked at import time."""
from __future__ import annotations

import subprocess
from unittest.mock import MagicMock, patch, PropertyMock

import pytest


# ---------------------------------------------------------------------------
# Module-level mock for Xlib.display.Display
# We patch at the module path used by window_tracker.py so the import works
# even in headless environments where Xlib cannot open a display.
# ---------------------------------------------------------------------------

def _make_display_mock() -> MagicMock:
    """Return a MagicMock that simulates the Xlib Display chain."""
    display_mock = MagicMock()
    screen_mock = MagicMock()
    root_mock = MagicMock()

    display_mock.screen.return_value = screen_mock
    screen_mock.root = root_mock

    return display_mock


@pytest.fixture()
def display_mock():
    return _make_display_mock()


@pytest.fixture()
def tracker(display_mock):
    """WindowTracker with Xlib.display.Display fully mocked."""
    with patch("sin_guide.overlay.window_tracker.Display", return_value=display_mock):
        from sin_guide.overlay.window_tracker import WindowTracker
        t = WindowTracker(window_title="Path of Exile 2")
        yield t


# ---------------------------------------------------------------------------
# is_game_focused
# ---------------------------------------------------------------------------

class TestIsGameFocused:
    def test_returns_true_when_subprocess_matches_title(self, tracker) -> None:
        # Arrange: _get_active_title_via_subprocess returns a matching title
        with patch.object(
            tracker, "_get_active_title_via_subprocess", return_value="Path of Exile 2"
        ):
            result = tracker.is_game_focused()

        assert result is True

    def test_returns_false_when_no_match(self, tracker) -> None:
        with patch.object(
            tracker, "_get_active_title_via_subprocess", return_value="Firefox"
        ), patch.object(
            tracker, "_get_focus_title_via_xlib", return_value="Firefox"
        ):
            result = tracker.is_game_focused()

        assert result is False

    def test_falls_back_to_xlib_when_subprocess_returns_none(self, tracker) -> None:
        with patch.object(
            tracker, "_get_active_title_via_subprocess", return_value=None
        ), patch.object(
            tracker, "_get_focus_title_via_xlib", return_value="Path of Exile 2"
        ):
            result = tracker.is_game_focused()

        assert result is True

    def test_returns_false_when_both_methods_return_none(self, tracker) -> None:
        with patch.object(
            tracker, "_get_active_title_via_subprocess", return_value=None
        ), patch.object(
            tracker, "_get_focus_title_via_xlib", return_value=None
        ):
            result = tracker.is_game_focused()

        assert result is False

    def test_case_insensitive_matching(self, tracker) -> None:
        with patch.object(
            tracker, "_get_active_title_via_subprocess", return_value="PATH OF EXILE 2"
        ):
            result = tracker.is_game_focused()

        assert result is True


# ---------------------------------------------------------------------------
# is_game_mapped
# ---------------------------------------------------------------------------

class TestIsGameMapped:
    def test_returns_false_when_game_window_is_none(self, tracker) -> None:
        # Arrange
        tracker.game_window = None

        # Act / Assert
        assert tracker.is_game_mapped() is False

    def test_returns_false_when_get_attributes_raises(self, tracker) -> None:
        # Arrange
        window_mock = MagicMock()
        window_mock.get_attributes.side_effect = Exception("X error")
        tracker.game_window = window_mock

        assert tracker.is_game_mapped() is False

    def test_returns_true_when_window_is_viewable(self, tracker) -> None:
        from Xlib import X
        window_mock = MagicMock()
        attrs_mock = MagicMock()
        attrs_mock.map_state = X.IsViewable
        window_mock.get_attributes.return_value = attrs_mock
        tracker.game_window = window_mock

        assert tracker.is_game_mapped() is True

    def test_returns_false_when_window_not_viewable(self, tracker) -> None:
        window_mock = MagicMock()
        attrs_mock = MagicMock()
        attrs_mock.map_state = 0  # not IsViewable
        window_mock.get_attributes.return_value = attrs_mock
        tracker.game_window = window_mock

        assert tracker.is_game_mapped() is False


# ---------------------------------------------------------------------------
# _is_poe2_process_running
# ---------------------------------------------------------------------------

class TestIsPoe2ProcessRunning:
    def test_returns_true_when_pgrep_succeeds(self, tracker) -> None:
        # Arrange
        mock_result = MagicMock()
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            result = tracker._is_poe2_process_running()

        assert result is True
        mock_run.assert_called_once()

    def test_returns_false_when_pgrep_fails(self, tracker) -> None:
        mock_result = MagicMock()
        mock_result.returncode = 1

        with patch("subprocess.run", return_value=mock_result):
            result = tracker._is_poe2_process_running()

        assert result is False

    def test_returns_false_on_exception(self, tracker) -> None:
        with patch("subprocess.run", side_effect=FileNotFoundError("pgrep not found")):
            result = tracker._is_poe2_process_running()

        assert result is False


# ---------------------------------------------------------------------------
# should_show_overlay
# ---------------------------------------------------------------------------

class TestShouldShowOverlay:
    def test_returns_true_when_game_is_focused(self, tracker) -> None:
        with patch.object(tracker, "is_game_focused", return_value=True):
            assert tracker.should_show_overlay() is True

    def test_returns_false_when_game_not_focused_and_no_overlay_id(self, tracker) -> None:
        with patch.object(tracker, "is_game_focused", return_value=False):
            assert tracker.should_show_overlay() is False

    def test_returns_true_when_overlay_window_is_focused(self, tracker, display_mock) -> None:
        # Arrange: game not focused but overlay window has focus
        focus_mock = MagicMock()
        focus_mock.id = 12345
        focus_result = MagicMock()
        focus_result.focus = focus_mock
        display_mock.get_input_focus.return_value = focus_result
        tracker.display = display_mock

        with patch.object(tracker, "is_game_focused", return_value=False):
            result = tracker.should_show_overlay(overlay_window_id=12345)

        assert result is True

    def test_returns_false_when_overlay_id_does_not_match(self, tracker, display_mock) -> None:
        focus_mock = MagicMock()
        focus_mock.id = 99999
        focus_result = MagicMock()
        focus_result.focus = focus_mock
        display_mock.get_input_focus.return_value = focus_result
        tracker.display = display_mock

        with patch.object(tracker, "is_game_focused", return_value=False):
            result = tracker.should_show_overlay(overlay_window_id=12345)

        assert result is False


# ---------------------------------------------------------------------------
# find_game_window
# ---------------------------------------------------------------------------

class TestFindGameWindow:
    def test_find_game_window_returns_none_when_no_match(self, tracker) -> None:
        # Arrange: root has no children matching the title
        root_mock = tracker.root
        tree_mock = MagicMock()
        tree_mock.children = []
        root_mock.query_tree.return_value = tree_mock

        result = tracker.find_game_window()

        assert result is None

    def test_find_game_window_sets_game_window(self, tracker) -> None:
        # Arrange: one child whose wm_name matches
        matching_child = MagicMock()
        matching_child.get_wm_name.return_value = "Path of Exile 2"
        matching_child.get_wm_class.return_value = None
        child_tree = MagicMock()
        child_tree.children = []
        matching_child.query_tree.return_value = child_tree

        root_tree = MagicMock()
        root_tree.children = [matching_child]
        tracker.root.query_tree.return_value = root_tree

        result = tracker.find_game_window()

        assert result is matching_child
        assert tracker.game_window is matching_child


# ---------------------------------------------------------------------------
# _get_active_title_via_subprocess
# ---------------------------------------------------------------------------

class TestGetActiveTitleViaSubprocess:
    def test_returns_title_when_xprop_succeeds(self, tracker) -> None:
        # Arrange: first xprop call returns window id, second returns title
        r1 = MagicMock()
        r1.returncode = 0
        r1.stdout = "_NET_ACTIVE_WINDOW(WINDOW): window id # 0x123456"

        r2 = MagicMock()
        r2.returncode = 0
        r2.stdout = '_NET_WM_NAME(UTF8_STRING) = "Path of Exile 2"\n'

        with patch("subprocess.run", side_effect=[r1, r2]):
            result = tracker._get_active_title_via_subprocess()

        assert result == "Path of Exile 2"

    def test_returns_none_when_first_xprop_fails(self, tracker) -> None:
        r1 = MagicMock()
        r1.returncode = 1
        r1.stdout = ""

        with patch("subprocess.run", return_value=r1):
            result = tracker._get_active_title_via_subprocess()

        assert result is None

    def test_returns_none_when_no_window_id_in_output(self, tracker) -> None:
        r1 = MagicMock()
        r1.returncode = 0
        r1.stdout = "some unrelated output"

        with patch("subprocess.run", return_value=r1):
            result = tracker._get_active_title_via_subprocess()

        assert result is None

    def test_returns_none_when_second_xprop_fails(self, tracker) -> None:
        r1 = MagicMock()
        r1.returncode = 0
        r1.stdout = "_NET_ACTIVE_WINDOW(WINDOW): window id # 0x123"

        r2 = MagicMock()
        r2.returncode = 1
        r2.stdout = ""

        with patch("subprocess.run", side_effect=[r1, r2]):
            result = tracker._get_active_title_via_subprocess()

        assert result is None

    def test_returns_none_on_exception(self, tracker) -> None:
        with patch("subprocess.run", side_effect=FileNotFoundError("xprop not found")):
            result = tracker._get_active_title_via_subprocess()

        assert result is None

    def test_returns_none_when_no_hash_in_output(self, tracker) -> None:
        # Output has 'window id' but no '#' separator
        r1 = MagicMock()
        r1.returncode = 0
        r1.stdout = "_NET_ACTIVE_WINDOW(WINDOW): window id 0x123"

        with patch("subprocess.run", return_value=r1):
            result = tracker._get_active_title_via_subprocess()

        assert result is None


# ---------------------------------------------------------------------------
# _get_focus_title_via_xlib
# ---------------------------------------------------------------------------

class TestGetFocusTitleViaXlib:
    def test_returns_none_when_get_input_focus_raises(self, tracker, display_mock) -> None:
        display_mock.get_input_focus.side_effect = Exception("X error")
        tracker.display = display_mock

        result = tracker._get_focus_title_via_xlib()

        assert result is None

    def test_returns_none_when_focus_is_none(self, tracker, display_mock) -> None:
        focus_result = MagicMock()
        focus_result.focus = None
        display_mock.get_input_focus.return_value = focus_result
        tracker.display = display_mock

        result = tracker._get_focus_title_via_xlib()

        assert result is None

    def test_returns_net_wm_name_via_atom(self, tracker, display_mock) -> None:
        # Arrange: focus window has _NET_WM_NAME property
        focus_mock = MagicMock()
        prop_mock = MagicMock()
        prop_mock.value = b"Path of Exile 2"
        focus_mock.get_full_property.return_value = prop_mock

        focus_result = MagicMock()
        focus_result.focus = focus_mock
        display_mock.get_input_focus.return_value = focus_result
        display_mock.intern_atom.return_value = 42
        tracker.display = display_mock

        result = tracker._get_focus_title_via_xlib()

        assert result == "Path of Exile 2"

    def test_falls_back_to_wm_name_when_no_net_wm_name(self, tracker, display_mock) -> None:
        # _NET_WM_NAME property returns None, fall back to get_wm_name()
        focus_mock = MagicMock()
        focus_mock.get_full_property.return_value = None
        focus_mock.get_wm_name.return_value = "Path of Exile 2"

        focus_result = MagicMock()
        focus_result.focus = focus_mock
        display_mock.get_input_focus.return_value = focus_result
        display_mock.intern_atom.return_value = 42
        tracker.display = display_mock

        result = tracker._get_focus_title_via_xlib()

        assert result == "Path of Exile 2"


# ---------------------------------------------------------------------------
# get_game_geometry
# ---------------------------------------------------------------------------

class TestGetGameGeometry:
    def test_returns_none_when_game_window_is_none(self, tracker) -> None:
        tracker.game_window = None
        assert tracker.get_game_geometry() is None

    def test_returns_geometry_dict_with_parent(self, tracker) -> None:
        # Arrange
        game_window = MagicMock()
        geom = MagicMock()
        geom.x = 5
        geom.y = 10
        geom.width = 1920
        geom.height = 1080
        game_window.get_geometry.return_value = geom

        parent = MagicMock()
        pgeom = MagicMock()
        pgeom.x = 100
        pgeom.y = 200
        parent.get_geometry.return_value = pgeom

        tree = MagicMock()
        tree.parent = parent
        game_window.query_tree.return_value = tree

        tracker.game_window = game_window

        result = tracker.get_game_geometry()

        assert result is not None
        assert result["width"] == 1920
        assert result["height"] == 1080
        assert result["x"] == 105   # pgeom.x + geom.x
        assert result["y"] == 210   # pgeom.y + geom.y

    def test_returns_none_on_exception(self, tracker) -> None:
        game_window = MagicMock()
        game_window.get_geometry.side_effect = Exception("X error")
        tracker.game_window = game_window

        assert tracker.get_game_geometry() is None


# ---------------------------------------------------------------------------
# cleanup
# ---------------------------------------------------------------------------

class TestCleanup:
    def test_cleanup_calls_display_close(self, tracker, display_mock) -> None:
        # Act
        tracker.cleanup()

        # Assert
        display_mock.close.assert_called_once()
