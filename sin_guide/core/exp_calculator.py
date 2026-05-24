import math


class ExpCalculator:
    def threshold(self, player_level: int) -> int:
        return 3 + math.floor(player_level / 16)

    def effective_difference(self, player_level: int, zone_level: int) -> int:
        threshold = self.threshold(player_level)
        diff = abs(player_level - zone_level)
        return max(0, diff - threshold)

    def penalty_multiplier(self, player_level: int, zone_level: int) -> float:
        eff_diff = self.effective_difference(player_level, zone_level)
        if eff_diff == 0:
            return 1.0
        if eff_diff == 1:
            return 0.95
        if eff_diff <= 3:
            return 0.75
        return 0.4

    def status_color(self, player_level: int, zone_level: int) -> str:
        eff_diff = self.effective_difference(player_level, zone_level)
        if eff_diff == 0:
            return "green"
        if eff_diff == 1:
            return "yellow"
        if eff_diff == 2:
            return "orange"
        return "red"

    def display(self, player_level: int, zone_level: int) -> str:
        threshold = self.threshold(player_level)
        min_level = player_level - threshold
        max_level = player_level + threshold
        eff_diff = self.effective_difference(player_level, zone_level)
        color = self.status_color(player_level, zone_level)
        if eff_diff == 0:
            return f"[{color}] {min_level} | {player_level} | {max_level}"
        return f"[{color}] ({eff_diff} levels off)"
