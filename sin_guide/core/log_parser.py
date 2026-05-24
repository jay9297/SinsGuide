import re
from dataclasses import dataclass
from enum import Enum, auto


class LogEventType(Enum):
    ENTERED_ZONE = auto()
    KILLED_BOSS = auto()
    QUEST_REWARD = auto()
    LEVEL_UP = auto()
    GENERATING_AREA = auto()
    CONNECTING_INSTANCE = auto()


@dataclass
class LogEvent:
    event_type: LogEventType
    data: str
    timestamp: str


class LogParser:
    PATTERNS = {
        LogEventType.ENTERED_ZONE: re.compile(
            r'\[SCENE\] Set Source \[(?!\(null\))([^\]]+)\]'
        ),
        LogEventType.KILLED_BOSS: re.compile(
            r"Killed ([^.]+)$"
        ),
        LogEventType.QUEST_REWARD: re.compile(
            r"Quest reward: ([^.]+)$"
        ),
        LogEventType.LEVEL_UP: re.compile(
            r"You have reached level (\d+)"
        ),
        LogEventType.GENERATING_AREA: re.compile(
            r'Generating level \d+ area "([^"]+)"'
        ),
        LogEventType.CONNECTING_INSTANCE: re.compile(
            r"Connecting to instance server at"
        ),
    }

    def parse_line(self, line: str) -> LogEvent | None:
        timestamp_match = re.match(r"^(\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2})\s+", line)
        timestamp = timestamp_match.group(1) if timestamp_match else ""
        content = line[timestamp_match.end():] if timestamp_match else line

        for event_type, pattern in self.PATTERNS.items():
            match = pattern.search(content)
            if match:
                data = match.group(1) if match.groups() else ""
                return LogEvent(event_type, data, timestamp)
        return None
