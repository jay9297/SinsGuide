import csv
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class TimerState:
    total_seconds: float = 0.0
    act_seconds: float = 0.0
    current_act: int = 1
    is_running: bool = False
    is_paused: bool = False
    _start_time: float | None = None
    _act_start_time: float | None = None
    splits: list[dict] = field(default_factory=list)


class CampaignTimer:
    def __init__(self, export_dir: Path):
        self.state = TimerState()
        self.export_dir = export_dir
        self.export_dir.mkdir(parents=True, exist_ok=True)
        self.csv_file = self.export_dir / "campaign_runs.csv"
        self._init_csv()

    def _init_csv(self):
        if not self.csv_file.exists():
            with open(self.csv_file, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "timestamp", "character", "act",
                    "act_seconds", "total_seconds"
                ])

    def start(self):
        if not self.state.is_running:
            self.state.is_running = True
            self.state.is_paused = False
            self.state._start_time = time.monotonic()
            self.state._act_start_time = time.monotonic()

    def pause(self):
        if self.state.is_running and not self.state.is_paused:
            elapsed = time.monotonic() - self.state._start_time
            act_elapsed = time.monotonic() - self.state._act_start_time
            self.state.total_seconds += elapsed
            self.state.act_seconds += act_elapsed
            self.state.is_paused = True
            self.state._start_time = None
            self.state._act_start_time = None

    def resume(self):
        if self.state.is_running and self.state.is_paused:
            self.state.is_paused = False
            self.state._start_time = time.monotonic()
            self.state._act_start_time = time.monotonic()

    def advance_act(self, character: str):
        if self.state.is_running and not self.state.is_paused:
            elapsed = time.monotonic() - self.state._act_start_time
            self.state.act_seconds += elapsed
            self._write_split(character)
            self.state.current_act += 1
            self.state.act_seconds = 0.0
            self.state._act_start_time = time.monotonic()

    def reset(self):
        self.state = TimerState()

    def _write_split(self, character: str):
        timestamp = datetime.now().isoformat()
        with open(self.csv_file, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                timestamp,
                character,
                self.state.current_act,
                round(self.state.act_seconds, 1),
                round(self.state.total_seconds, 1),
            ])

    def get_display(self) -> str:
        total = self.state.total_seconds
        act = self.state.act_seconds
        if self.state.is_running and not self.state.is_paused and self.state._start_time:
            elapsed = time.monotonic() - self.state._start_time
            act_elapsed = time.monotonic() - self.state._act_start_time
            total += elapsed
            act += act_elapsed
        total_str = self._format_time(total)
        act_str = self._format_time(act)
        return f"{total_str} | A{self.state.current_act} | {act_str}"

    @staticmethod
    def _format_time(seconds: float) -> str:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        return f"{minutes}:{secs:02d}"
