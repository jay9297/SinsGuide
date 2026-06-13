# tests/conftest.py
from __future__ import annotations

import os

# Must be set before PySide6 is imported anywhere in the process.
os.environ["QT_QPA_PLATFORM"] = "offscreen"

import io
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest
from PIL import Image, ImageChops

from sin_guide.core.guide_engine import GuideStep

SNAPSHOTS_DIR = Path(__file__).parent / "visual" / "snapshots"
# Actual renders written here on comparison failure so CI can upload them.
ACTUAL_SNAPSHOTS_DIR = Path(__file__).parent / "visual" / "snapshots_actual"
_TEST_FONT_PATH = Path(__file__).parent / "visual" / "fonts" / "DejaVuSans.ttf"


# ---------------------------------------------------------------------------
# Environment isolation
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _isolate_xdg_config(monkeypatch):
    """Strip XDG_CONFIG_HOME so ConfigManager falls back to Path.home().

    GitHub-hosted runners export XDG_CONFIG_HOME, which would bypass the
    Path.home() patching the config tests rely on and leak state into the
    runner's real config directory.
    """
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)


# ---------------------------------------------------------------------------
# Deterministic font
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session", autouse=True)
def _deterministic_font(qapp):
    """Load the bundled DejaVu Sans at a fixed *pixel* size so that text
    metrics are identical on every machine.

    Point sizes are scaled by DPI, which varies between CI runners and
    developer desktops; pixel sizes are not.  The bundled TTF ensures the
    same glyph metrics regardless of which fonts happen to be installed on
    the host.
    """
    from PySide6.QtGui import QFont, QFontDatabase
    font_id = QFontDatabase.addApplicationFont(str(_TEST_FONT_PATH))
    if font_id < 0:
        pytest.fail(
            f"Could not load test font {_TEST_FONT_PATH}. "
            "Check that tests/visual/fonts/DejaVuSans.ttf is committed."
        )
    families = QFontDatabase.applicationFontFamilies(font_id)
    font = QFont(families[0])
    font.setPixelSize(13)
    qapp.setFont(font)
    yield


# ---------------------------------------------------------------------------
# GuideStep factory
# ---------------------------------------------------------------------------

def make_step(
    *,
    id: str = "step_001",
    act: int = 1,
    zone: str = "The Riverbank",
    step_number: int = 1,
    description: str = "Kill Renly",
    step_type: str = "kill",
    target: str = "Renly",
    hint: str = "",
    tags: list[str] | None = None,
    next_steps: list[str] | None = None,
    auto_advance_trigger: dict[str, Any] | None = None,
) -> GuideStep:
    return GuideStep(
        id=id,
        act=act,
        zone=zone,
        step_number=step_number,
        description=description,
        step_type=step_type,
        target=target,
        hint=hint,
        tags=tags or ["mandatory"],
        next_steps=next_steps or [],
        auto_advance_trigger=auto_advance_trigger,
    )


# ---------------------------------------------------------------------------
# Mock fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def mock_config_values() -> dict[str, Any]:
    """Override individual config values per-test by updating this dict."""
    return {
        "overlay.transparency": 0.75,
        "overlay.font_size": 12,
        "overlay.width": 220,
        "overlay.x": -1,
        "overlay.y": -1,
        "overlay.show_timer": True,
        "overlay.show_effective_exp": False,
        "overlay.max_visible_lines": 5,
        "guide.league_start": True,
        "guide.show_optionals": True,
        "guide.character_name": "",
    }


@pytest.fixture()
def mock_config(mock_config_values):
    config = MagicMock()
    config.get.side_effect = lambda key, default=None: mock_config_values.get(key, default)
    config.set = MagicMock()
    return config


@pytest.fixture()
def mock_guide():
    guide = MagicMock()
    guide.get_visible_steps.return_value = []
    guide.current_step_id = "step_001"
    return guide


@pytest.fixture()
def mock_timer():
    timer = MagicMock()
    timer.get_display.return_value = "0:32 | A1 | 0:32"
    return timer


@pytest.fixture()
def mock_exp_calc():
    exp = MagicMock()
    exp.display.return_value = "2 levels under — 0% penalty"
    return exp


# ---------------------------------------------------------------------------
# Overlay factory
# ---------------------------------------------------------------------------

@pytest.fixture()
def make_overlay(qtbot, mock_config, mock_guide, mock_timer, mock_exp_calc, mock_config_values):
    """
    Returns a factory function.  Call it inside a test to create a configured
    OverlayWindow with deterministic content.

    Args:
        steps:           List of GuideStep objects shown in the step list.
        timer_display:   String returned by timer.get_display().
        player_level:    If set, _get_player_level() is patched to return this
                         value so the exp label becomes visible.
        config_overrides: Dict of "overlay.X" keys to override for this test.
    """
    created: list = []

    def _factory(
        steps: list[GuideStep] | None = None,
        timer_display: str = "0:32 | A1 | 0:32",
        player_level: int | None = None,
        config_overrides: dict[str, Any] | None = None,
    ):
        # Late import -- QT_QPA_PLATFORM is already set by the time this runs.
        from sin_guide.overlay.main_window import OverlayWindow

        if config_overrides:
            mock_config_values.update(config_overrides)

        mock_guide.get_visible_steps.return_value = steps or []
        mock_timer.get_display.return_value = timer_display

        overlay = OverlayWindow(mock_config, mock_guide, mock_timer, mock_exp_calc)

        if player_level is not None:
            overlay._get_player_level = lambda: player_level

        qtbot.addWidget(overlay)
        overlay.show()
        qtbot.waitExposed(overlay)

        # Drive one deterministic update so timer/exp/steps are rendered.
        overlay._update_display()

        created.append(overlay)
        return overlay

    yield _factory

    for w in created:
        w.close()


# ---------------------------------------------------------------------------
# Snapshot assertion helper
# ---------------------------------------------------------------------------

def _qpixmap_to_pil(pixmap) -> Image.Image:
    """Convert a QPixmap to a PIL RGBA Image via PNG bytes."""
    from PySide6.QtCore import QBuffer, QIODevice
    buf = QBuffer()
    buf.open(QIODevice.OpenModeFlag.WriteOnly)
    pixmap.save(buf, "PNG")
    buf.close()
    return Image.open(io.BytesIO(bytes(buf.data()))).convert("RGBA")


def _images_match(actual: Image.Image, baseline: Image.Image, tolerance: float = 0.02) -> tuple[bool, float]:
    """
    Compare two RGBA images.  Returns (match, diff_ratio).

    diff_ratio is the fraction of pixels whose per-channel mean absolute
    difference exceeds 5/255.  A tolerance of 0.02 (2%) accommodates
    minor sub-pixel and font-hinting differences between Qt versions
    without hiding real layout regressions.
    """
    if actual.size != baseline.size:
        return False, 1.0

    diff = ImageChops.difference(actual, baseline)
    pixels = list(diff.getdata())
    total = len(pixels)
    differing = sum(1 for p in pixels if sum(p) / len(p) > 5)
    ratio = differing / total
    return ratio <= tolerance, ratio


@pytest.fixture()
def assert_matches_snapshot(request):
    """
    Fixture that provides a callable: assert_matches_snapshot(pixmap, name).

    Compares the rendered pixmap against a committed baseline PNG.  On
    mismatch the actual render is written to tests/visual/snapshots_actual/
    so CI can upload it as an artifact for inspection.

    A missing baseline is a hard failure — it is NOT silently created.  To
    add or regenerate baselines, trigger the update-snapshots GitHub Actions
    workflow (or run `pytest --update-snapshots tests/visual/` locally).
    This prevents the self-comparison trap where auto-creating a baseline in
    the same run that tests it makes every test trivially pass.

    Pass --update-snapshots to regenerate all baselines:
        pytest --update-snapshots tests/visual/
    """
    update = request.config.getoption("--update-snapshots", default=False)

    def _assert(pixmap, name: str, tolerance: float = 0.02):
        SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
        baseline_path = SNAPSHOTS_DIR / f"{name}.png"
        actual = _qpixmap_to_pil(pixmap)

        if update:
            actual.save(baseline_path)
            return  # Baseline updated — pass unconditionally.

        if not baseline_path.exists():
            pytest.fail(
                f"No baseline snapshot '{name}' found at {baseline_path}. "
                "Trigger the update-snapshots workflow or run "
                "`pytest --update-snapshots tests/visual/` to create it."
            )

        baseline = Image.open(baseline_path).convert("RGBA")
        match, ratio = _images_match(actual, baseline, tolerance)
        if not match:
            ACTUAL_SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
            actual.save(ACTUAL_SNAPSHOTS_DIR / f"{name}_actual.png")
        assert match, (
            f"Visual snapshot '{name}' differs by {ratio:.1%} "
            f"(tolerance {tolerance:.1%}). "
            f"Actual saved to tests/visual/snapshots_actual/{name}_actual.png. "
            f"Trigger the update-snapshots workflow if the change is intentional."
        )

    return _assert


def pytest_addoption(parser):
    parser.addoption(
        "--update-snapshots",
        action="store_true",
        default=False,
        help="Regenerate all visual snapshot baselines.",
    )
