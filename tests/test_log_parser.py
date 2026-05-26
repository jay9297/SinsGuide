"""Tests for LogParser — regex pattern matching per LogEventType."""
from __future__ import annotations

import pytest

from sin_guide.core.log_parser import LogEvent, LogEventType, LogParser


@pytest.fixture()
def parser() -> LogParser:
    return LogParser()


def make_line(content: str, with_timestamp: bool = True) -> str:
    """Build a realistic log line with an optional timestamp prefix."""
    if with_timestamp:
        return f"2024/01/15 12:34:56 {content}"
    return content


class TestEnteredZone:
    def test_entered_zone_returns_event(self, parser: LogParser) -> None:
        # Arrange
        line = make_line("[SCENE] Set Source [The Riverbank]")

        # Act
        event = parser.parse_line(line)

        # Assert
        assert event is not None
        assert event.event_type == LogEventType.ENTERED_ZONE
        assert event.data == "The Riverbank"

    def test_entered_zone_captures_zone_name(self, parser: LogParser) -> None:
        line = make_line("[SCENE] Set Source [Clearfell]")
        event = parser.parse_line(line)
        assert event is not None
        assert event.data == "Clearfell"

    def test_null_zone_is_rejected(self, parser: LogParser) -> None:
        # The (null) zone name should NOT produce an ENTERED_ZONE event
        line = make_line("[SCENE] Set Source [(null)]")
        event = parser.parse_line(line)
        # Either None or a different event type — must not be ENTERED_ZONE with (null)
        if event is not None:
            assert event.event_type != LogEventType.ENTERED_ZONE or event.data != "(null)"

    def test_timestamp_is_captured(self, parser: LogParser) -> None:
        line = make_line("[SCENE] Set Source [The Grelwood]")
        event = parser.parse_line(line)
        assert event is not None
        assert event.timestamp == "2024/01/15 12:34:56"


class TestKilledBoss:
    def test_killed_boss_returns_event(self, parser: LogParser) -> None:
        # Arrange
        line = make_line("Killed Renly")

        # Act
        event = parser.parse_line(line)

        # Assert
        assert event is not None
        assert event.event_type == LogEventType.KILLED_BOSS
        assert event.data == "Renly"

    def test_killed_boss_captures_name(self, parser: LogParser) -> None:
        line = make_line("Killed The Crowbell")
        event = parser.parse_line(line)
        assert event is not None
        assert event.data == "The Crowbell"


class TestQuestReward:
    def test_quest_reward_returns_event(self, parser: LogParser) -> None:
        # Arrange
        line = make_line("Quest reward: Fireball")

        # Act
        event = parser.parse_line(line)

        # Assert
        assert event is not None
        assert event.event_type == LogEventType.QUEST_REWARD
        assert event.data == "Fireball"

    def test_quest_reward_captures_reward_name(self, parser: LogParser) -> None:
        line = make_line("Quest reward: Herald of Ice")
        event = parser.parse_line(line)
        assert event is not None
        assert event.data == "Herald of Ice"


class TestLevelUp:
    def test_level_up_returns_event(self, parser: LogParser) -> None:
        # Arrange
        line = make_line("You have reached level 10")

        # Act
        event = parser.parse_line(line)

        # Assert
        assert event is not None
        assert event.event_type == LogEventType.LEVEL_UP
        assert event.data == "10"

    @pytest.mark.parametrize("level", [1, 15, 50, 100])
    def test_level_up_various_levels(self, parser: LogParser, level: int) -> None:
        line = make_line(f"You have reached level {level}")
        event = parser.parse_line(line)
        assert event is not None
        assert event.event_type == LogEventType.LEVEL_UP
        assert event.data == str(level)


class TestGeneratingArea:
    def test_generating_area_returns_event(self, parser: LogParser) -> None:
        # Arrange
        line = make_line('Generating level 5 area "The Grelwood"')

        # Act
        event = parser.parse_line(line)

        # Assert
        assert event is not None
        assert event.event_type == LogEventType.GENERATING_AREA
        assert event.data == "The Grelwood"

    def test_generating_area_captures_name(self, parser: LogParser) -> None:
        line = make_line('Generating level 32 area "The Azak Bog"')
        event = parser.parse_line(line)
        assert event is not None
        assert event.data == "The Azak Bog"


class TestConnectingInstance:
    def test_connecting_instance_returns_event(self, parser: LogParser) -> None:
        # Arrange
        line = make_line("Connecting to instance server at 192.168.1.1:6112")

        # Act
        event = parser.parse_line(line)

        # Assert
        assert event is not None
        assert event.event_type == LogEventType.CONNECTING_INSTANCE
        assert event.data == ""  # no capture group for this pattern

    def test_connecting_instance_data_is_empty_string(self, parser: LogParser) -> None:
        line = make_line("Connecting to instance server at 10.0.0.1:1234")
        event = parser.parse_line(line)
        assert event is not None
        assert event.data == ""


class TestNoTimestamp:
    def test_line_without_timestamp_is_still_parsed(self, parser: LogParser) -> None:
        # Arrange — no timestamp prefix
        line = make_line("You have reached level 7", with_timestamp=False)

        # Act
        event = parser.parse_line(line)

        # Assert — still parsed, but timestamp is empty
        assert event is not None
        assert event.event_type == LogEventType.LEVEL_UP
        assert event.timestamp == ""

    def test_line_without_timestamp_has_empty_timestamp(self, parser: LogParser) -> None:
        line = make_line("[SCENE] Set Source [Ogham Village]", with_timestamp=False)
        event = parser.parse_line(line)
        assert event is not None
        assert event.timestamp == ""


class TestUnmatchedLine:
    def test_unmatched_line_returns_none(self, parser: LogParser) -> None:
        # Arrange
        line = make_line("This line matches no pattern at all")

        # Act
        event = parser.parse_line(line)

        # Assert
        assert event is None

    def test_empty_line_returns_none(self, parser: LogParser) -> None:
        assert parser.parse_line("") is None

    def test_whitespace_only_returns_none(self, parser: LogParser) -> None:
        assert parser.parse_line("   ") is None

    @pytest.mark.parametrize("line", [
        "2024/01/15 12:34:56 [INFO] Loading assets...",
        "2024/01/15 12:34:56 Connected to login server",
        "2024/01/15 12:34:56 Debug: memory 1024mb",
    ])
    def test_various_unmatched_lines_return_none(self, parser: LogParser, line: str) -> None:
        assert parser.parse_line(line) is None


class TestLogEventDataclass:
    def test_log_event_fields(self) -> None:
        # Arrange / Act
        event = LogEvent(
            event_type=LogEventType.LEVEL_UP,
            data="42",
            timestamp="2024/01/15 12:00:00",
        )

        # Assert
        assert event.event_type == LogEventType.LEVEL_UP
        assert event.data == "42"
        assert event.timestamp == "2024/01/15 12:00:00"
