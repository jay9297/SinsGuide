"""Tests for CampaignTimer — start/pause/resume, splits, CSV, display.

NOTE: time.monotonic must be patched as 'sin_guide.core.timer.time.monotonic'
because timer.py uses `import time` and calls `time.monotonic()` directly.
Also, _start_time=0.0 is falsy so get_display() skips the live-elapsed branch;
tests that exercise get_display() while running must use a non-zero start value.
"""
from __future__ import annotations

import csv
from pathlib import Path
from unittest.mock import patch

import pytest

from sin_guide.core.timer import CampaignTimer, TimerState

# Canonical patch target
_MONO = "sin_guide.core.timer.time.monotonic"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_timer(tmp_path: Path) -> CampaignTimer:
    return CampaignTimer(export_dir=tmp_path / "runs")


# ---------------------------------------------------------------------------
# CSV initialisation
# ---------------------------------------------------------------------------

class TestCsvInit:
    def test_csv_file_created_on_init(self, tmp_path: Path) -> None:
        # Arrange / Act
        timer = make_timer(tmp_path)

        # Assert
        assert timer.csv_file.exists()

    def test_csv_has_header_row(self, tmp_path: Path) -> None:
        timer = make_timer(tmp_path)
        with open(timer.csv_file, newline="") as f:
            rows = list(csv.reader(f))
        assert rows[0] == ["timestamp", "character", "act", "act_seconds", "total_seconds"]

    def test_duplicate_init_does_not_overwrite_csv(self, tmp_path: Path) -> None:
        # Arrange — write a split via first timer
        export_dir = tmp_path / "runs"
        t1 = CampaignTimer(export_dir=export_dir)

        # start=1.0 (truthy), advance at t=31.0
        with patch(_MONO, side_effect=[1.0, 1.0, 31.0, 31.0]):
            t1.start()
            t1.advance_act("Hero")

        # Act — second timer on same dir should not truncate the file
        t2 = CampaignTimer(export_dir=export_dir)

        with open(t2.csv_file, newline="") as f:
            rows = list(csv.reader(f))

        # Header + at least the one split written by t1
        assert len(rows) >= 2


# ---------------------------------------------------------------------------
# Start / pause / resume
# ---------------------------------------------------------------------------

class TestStartPauseResume:
    def test_start_sets_running(self, tmp_path: Path) -> None:
        timer = make_timer(tmp_path)
        with patch(_MONO, return_value=1.0):
            timer.start()
        assert timer.state.is_running is True
        assert timer.state.is_paused is False

    def test_start_is_idempotent(self, tmp_path: Path) -> None:
        timer = make_timer(tmp_path)
        with patch(_MONO, return_value=1.0):
            timer.start()
            timer.start()  # second call should be a no-op
        assert timer.state.is_running is True

    def test_pause_accumulates_seconds(self, tmp_path: Path) -> None:
        # Arrange: start at t=1, pause at t=11 → 10 s elapsed
        timer = make_timer(tmp_path)
        with patch(_MONO, side_effect=[1.0, 1.0, 11.0, 11.0]):
            timer.start()
            timer.pause()

        # Assert
        assert timer.state.total_seconds == pytest.approx(10.0)
        assert timer.state.act_seconds == pytest.approx(10.0)
        assert timer.state.is_paused is True

    def test_resume_clears_paused_flag(self, tmp_path: Path) -> None:
        timer = make_timer(tmp_path)
        with patch(_MONO, side_effect=[1.0, 1.0, 6.0, 6.0, 6.0, 6.0]):
            timer.start()
            timer.pause()
            timer.resume()
        assert timer.state.is_paused is False

    def test_pause_resume_accumulates_correctly(self, tmp_path: Path) -> None:
        # start=1, pause=6 (5 s), resume=6, pause=16 (10 s) → total=15
        timer = make_timer(tmp_path)
        monotonic_values = [
            1.0, 1.0,    # start
            6.0, 6.0,    # first pause (5 s elapsed)
            6.0, 6.0,    # resume (reset start time)
            16.0, 16.0,  # second pause (10 s elapsed)
        ]
        with patch(_MONO, side_effect=monotonic_values):
            timer.start()
            timer.pause()
            timer.resume()
            timer.pause()

        assert timer.state.total_seconds == pytest.approx(15.0)

    def test_pause_without_start_does_nothing(self, tmp_path: Path) -> None:
        timer = make_timer(tmp_path)
        timer.pause()  # should not raise
        assert timer.state.total_seconds == pytest.approx(0.0)

    def test_resume_without_pause_does_nothing(self, tmp_path: Path) -> None:
        timer = make_timer(tmp_path)
        with patch(_MONO, side_effect=[1.0, 1.0]):
            timer.start()
            timer.resume()  # not paused, should be a no-op
        assert timer.state.is_paused is False


# ---------------------------------------------------------------------------
# advance_act
# ---------------------------------------------------------------------------

class TestAdvanceAct:
    def test_advance_act_writes_csv_row(self, tmp_path: Path) -> None:
        # Arrange: start=1, advance at t=61 → 60 s act time
        timer = make_timer(tmp_path)
        with patch(_MONO, side_effect=[1.0, 1.0, 61.0, 61.0]):
            timer.start()
            timer.advance_act("Hero")

        with open(timer.csv_file, newline="") as f:
            rows = list(csv.reader(f))

        # Header + one data row
        assert len(rows) == 2
        assert rows[1][1] == "Hero"   # character
        assert rows[1][2] == "1"      # act number before increment
        assert float(rows[1][3]) == pytest.approx(60.0)  # act_seconds

    def test_advance_act_increments_act_counter(self, tmp_path: Path) -> None:
        timer = make_timer(tmp_path)
        with patch(_MONO, side_effect=[1.0, 1.0, 31.0, 31.0]):
            timer.start()
            timer.advance_act("Hero")
        assert timer.state.current_act == 2

    def test_advance_act_resets_act_seconds(self, tmp_path: Path) -> None:
        timer = make_timer(tmp_path)
        with patch(_MONO, side_effect=[1.0, 1.0, 31.0, 31.0]):
            timer.start()
            timer.advance_act("Hero")
        assert timer.state.act_seconds == pytest.approx(0.0)

    def test_advance_act_does_nothing_when_not_running(self, tmp_path: Path) -> None:
        timer = make_timer(tmp_path)
        timer.advance_act("Hero")  # not started
        assert timer.state.current_act == 1

    def test_multiple_advances_write_multiple_rows(self, tmp_path: Path) -> None:
        timer = make_timer(tmp_path)
        with patch(_MONO, side_effect=[
            1.0, 1.0,    # start
            31.0, 31.0,  # first advance (30 s)
            61.0, 61.0,  # second advance (30 s since reset)
        ]):
            timer.start()
            timer.advance_act("Hero")
            timer.advance_act("Hero")

        with open(timer.csv_file, newline="") as f:
            rows = list(csv.reader(f))
        assert len(rows) == 3  # header + 2 splits


# ---------------------------------------------------------------------------
# reset
# ---------------------------------------------------------------------------

class TestReset:
    def test_reset_clears_all_state(self, tmp_path: Path) -> None:
        timer = make_timer(tmp_path)
        with patch(_MONO, side_effect=[1.0, 1.0, 11.0, 11.0]):
            timer.start()
            timer.pause()

        timer.reset()

        assert timer.state.total_seconds == pytest.approx(0.0)
        assert timer.state.act_seconds == pytest.approx(0.0)
        assert timer.state.is_running is False
        assert timer.state.is_paused is False
        assert timer.state.current_act == 1

    def test_can_restart_after_reset(self, tmp_path: Path) -> None:
        timer = make_timer(tmp_path)
        with patch(_MONO, side_effect=[1.0, 1.0]):
            timer.start()
        timer.reset()
        with patch(_MONO, side_effect=[1.0, 1.0]):
            timer.start()
        assert timer.state.is_running is True


# ---------------------------------------------------------------------------
# get_display
# ---------------------------------------------------------------------------

class TestGetDisplay:
    def test_display_format_while_running(self, tmp_path: Path) -> None:
        # _start_time must be non-zero: 0.0 is falsy and short-circuits the
        # `self.state._start_time` guard in get_display().
        # start=1.0, read=91.0 → 90 s elapsed = "1:30"
        timer = make_timer(tmp_path)
        with patch(_MONO, side_effect=[1.0, 1.0, 91.0, 91.0]):
            timer.start()
            result = timer.get_display()

        assert "| A1 |" in result
        assert "1:30" in result  # 90 seconds

    def test_display_when_not_started(self, tmp_path: Path) -> None:
        timer = make_timer(tmp_path)
        result = timer.get_display()
        assert "0:00" in result
        assert "A1" in result

    def test_display_shows_correct_act(self, tmp_path: Path) -> None:
        # advance_act needs _act_start_time to be truthy too
        timer = make_timer(tmp_path)
        with patch(_MONO, side_effect=[1.0, 1.0, 11.0, 11.0]):
            timer.start()
            timer.advance_act("Hero")
        # After advance, is_running=True but _act_start_time reset to 11.0 (truthy)
        with patch(_MONO, side_effect=[11.0, 11.0]):
            result = timer.get_display()
        assert "A2" in result


# ---------------------------------------------------------------------------
# _format_time
# ---------------------------------------------------------------------------

class TestFormatTime:
    @pytest.mark.parametrize("seconds, expected", [
        (0,     "0:00"),
        (59,    "0:59"),
        (60,    "1:00"),
        (90,    "1:30"),
        (3599,  "59:59"),
        (3600,  "1:00:00"),
        (3661,  "1:01:01"),
        (7322,  "2:02:02"),
    ])
    def test_format_time_parametrized(self, seconds: float, expected: str) -> None:
        # Arrange / Act
        result = CampaignTimer._format_time(seconds)

        # Assert
        assert result == expected

    def test_format_time_no_hours_omits_hour_segment(self) -> None:
        result = CampaignTimer._format_time(125.9)
        assert ":" in result
        parts = result.split(":")
        assert len(parts) == 2  # MM:SS only

    def test_format_time_with_hours_has_three_segments(self) -> None:
        result = CampaignTimer._format_time(3700.0)
        parts = result.split(":")
        assert len(parts) == 3  # H:MM:SS
