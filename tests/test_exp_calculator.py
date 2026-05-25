"""Tests for ExpCalculator — pure math, parametrized branch coverage."""
from __future__ import annotations


import pytest

from sin_guide.core.exp_calculator import ExpCalculator


@pytest.fixture()
def calc() -> ExpCalculator:
    return ExpCalculator()


class TestThreshold:
    @pytest.mark.parametrize("player_level, expected", [
        (1,  3),   # 3 + floor(1/16) = 3
        (15, 3),   # 3 + floor(15/16) = 3
        (16, 4),   # 3 + floor(16/16) = 4
        (32, 5),   # 3 + floor(32/16) = 5
        (48, 6),   # 3 + floor(48/16) = 6
        (64, 7),   # 3 + floor(64/16) = 7
        (80, 8),   # 3 + floor(80/16) = 8
    ])
    def test_threshold_values(self, calc: ExpCalculator, player_level: int, expected: int) -> None:
        assert calc.threshold(player_level) == expected


class TestEffectiveDifference:
    def test_zero_when_same_level(self, calc: ExpCalculator) -> None:
        # Arrange / Act / Assert
        assert calc.effective_difference(20, 20) == 0

    def test_zero_when_diff_within_threshold(self, calc: ExpCalculator) -> None:
        # threshold at level 20 is 3+floor(20/16)=4; diff of 4 → eff_diff=0
        assert calc.effective_difference(20, 24) == 0

    def test_one_when_one_beyond_threshold(self, calc: ExpCalculator) -> None:
        # threshold=4 at lvl20; diff of 5 → eff_diff=1
        assert calc.effective_difference(20, 25) == 1

    def test_never_negative(self, calc: ExpCalculator) -> None:
        assert calc.effective_difference(20, 18) == 0

    @pytest.mark.parametrize("player_level, zone_level, expected_eff", [
        (10, 10, 0),   # same level
        (10, 13, 0),   # diff=3=threshold → eff=0
        (10, 14, 1),   # diff=4 → eff=1
        (10, 16, 3),   # diff=6 → eff=3
        (10, 17, 4),   # diff=7 → eff=4
    ])
    def test_effective_difference_parametrized(
        self, calc: ExpCalculator, player_level: int, zone_level: int, expected_eff: int
    ) -> None:
        assert calc.effective_difference(player_level, zone_level) == expected_eff


class TestPenaltyMultiplier:
    def test_no_penalty_at_eff_diff_zero(self, calc: ExpCalculator) -> None:
        # Arrange: same level → eff_diff=0
        result = calc.penalty_multiplier(20, 20)
        assert result == pytest.approx(1.0)

    def test_five_percent_penalty_at_eff_diff_one(self, calc: ExpCalculator) -> None:
        # eff_diff=1 → 0.95
        result = calc.penalty_multiplier(20, 25)
        assert result == pytest.approx(0.95)

    def test_twenty_five_percent_penalty_at_eff_diff_two(self, calc: ExpCalculator) -> None:
        # eff_diff=2 → 0.75
        result = calc.penalty_multiplier(20, 26)
        assert result == pytest.approx(0.75)

    def test_twenty_five_percent_penalty_at_eff_diff_three(self, calc: ExpCalculator) -> None:
        # eff_diff=3 → 0.75 (still in <=3 branch)
        result = calc.penalty_multiplier(20, 27)
        assert result == pytest.approx(0.75)

    def test_sixty_percent_penalty_at_eff_diff_four_plus(self, calc: ExpCalculator) -> None:
        # eff_diff=4 → 0.4
        result = calc.penalty_multiplier(20, 28)
        assert result == pytest.approx(0.4)

    @pytest.mark.parametrize("eff_diff_offset, expected_mult", [
        (0, 1.0),
        (1, 0.95),
        (2, 0.75),
        (3, 0.75),
        (4, 0.4),
        (10, 0.4),
    ])
    def test_penalty_multiplier_parametrized(
        self, calc: ExpCalculator, eff_diff_offset: int, expected_mult: float
    ) -> None:
        # Use level 1 (threshold=3). zone_level = player + threshold + eff_diff_offset
        player_level = 1
        threshold = calc.threshold(player_level)
        zone_level = player_level + threshold + eff_diff_offset
        result = calc.penalty_multiplier(player_level, zone_level)
        assert result == pytest.approx(expected_mult)


class TestStatusColor:
    @pytest.mark.parametrize("eff_diff_offset, expected_color", [
        (0, "green"),
        (1, "yellow"),
        (2, "orange"),
        (3, "red"),
        (5, "red"),
    ])
    def test_status_color_branches(
        self, calc: ExpCalculator, eff_diff_offset: int, expected_color: str
    ) -> None:
        # Arrange: player_level=1, threshold=3
        player_level = 1
        threshold = calc.threshold(player_level)
        zone_level = player_level + threshold + eff_diff_offset
        assert calc.status_color(player_level, zone_level) == expected_color

    def test_green_when_in_safe_range(self, calc: ExpCalculator) -> None:
        assert calc.status_color(20, 20) == "green"

    def test_yellow_at_one_over(self, calc: ExpCalculator) -> None:
        # threshold at lvl10 = 3; diff=4 → eff=1 → yellow
        assert calc.status_color(10, 14) == "yellow"

    def test_orange_at_two_over(self, calc: ExpCalculator) -> None:
        assert calc.status_color(10, 15) == "orange"

    def test_red_at_three_or_more(self, calc: ExpCalculator) -> None:
        assert calc.status_color(10, 16) == "red"
        assert calc.status_color(10, 20) == "red"


class TestDisplay:
    def test_display_no_penalty_shows_range(self, calc: ExpCalculator) -> None:
        # Arrange
        player_level = 16
        zone_level = 16
        threshold = calc.threshold(player_level)  # 4

        # Act
        result = calc.display(player_level, zone_level)

        # Assert
        expected_min = player_level - threshold
        expected_max = player_level + threshold
        assert f"{expected_min} | {player_level} | {expected_max}" in result
        assert "[green]" in result

    def test_display_with_penalty_shows_levels_off(self, calc: ExpCalculator) -> None:
        # Arrange: eff_diff > 0
        player_level = 10
        zone_level = 20  # well above threshold
        eff_diff = calc.effective_difference(player_level, zone_level)

        # Act
        result = calc.display(player_level, zone_level)

        # Assert
        assert f"({eff_diff} levels off)" in result

    @pytest.mark.parametrize("player_level, zone_level", [
        (1, 1),
        (20, 20),
        (50, 50),
    ])
    def test_display_on_level_includes_green(
        self, calc: ExpCalculator, player_level: int, zone_level: int
    ) -> None:
        result = calc.display(player_level, zone_level)
        assert "[green]" in result

    @pytest.mark.parametrize("player_level, zone_level", [
        (10, 20),
        (5, 15),
    ])
    def test_display_off_level_includes_color_and_diff(
        self, calc: ExpCalculator, player_level: int, zone_level: int
    ) -> None:
        result = calc.display(player_level, zone_level)
        eff_diff = calc.effective_difference(player_level, zone_level)
        assert f"({eff_diff} levels off)" in result
