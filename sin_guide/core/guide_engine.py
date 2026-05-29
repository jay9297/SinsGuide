import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class GuideStep:
    id: str
    act: int
    zone: str
    step_number: int
    description: str
    step_type: str
    target: str
    hint: str
    tags: list[str]
    next_steps: list[str]
    auto_advance_trigger: dict[str, Any] | None


class GuideEngine:
    def __init__(self, guide_path: Path):
        self.guide_path = guide_path
        self.steps: dict[str, GuideStep] = {}
        self.current_step_id: str | None = None
        self.current_zone: str | None = None
        self._load_guide()

    def _load_guide(self):
        if not self.guide_path.exists():
            return
        with open(self.guide_path, "r") as f:
            data = json.load(f)
        for step_data in data.get("steps", []):
            step = GuideStep(
                id=step_data["id"],
                act=step_data["act"],
                zone=step_data["zone"],
                step_number=step_data["step_number"],
                description=step_data["description"],
                step_type=step_data.get("type", "generic"),
                target=step_data.get("target", ""),
                hint=step_data.get("hint", ""),
                tags=step_data.get("tags", []),
                next_steps=step_data.get("next_steps", []),
                auto_advance_trigger=step_data.get("auto_advance_trigger"),
            )
            self.steps[step.id] = step
        if self.steps:
            self.current_step_id = min(self.steps.keys(), key=lambda k: self.steps[k].step_number)

    def get_visible_steps(self, league_start: bool, show_optionals: bool, max_lines: int = 5) -> list[GuideStep]:
        if not self.current_step_id or self.current_step_id not in self.steps:
            return []

        current = self.steps[self.current_step_id]
        target_zone = self.current_zone if self.current_zone else current.zone
        visible = []

        for sid, step in sorted(self.steps.items(), key=lambda x: x[1].step_number):
            if not self._should_show(step, league_start, show_optionals):
                continue
            if step.zone == target_zone:
                visible.append(step)
            if len(visible) >= max_lines:
                break

        return visible

    def _should_show(self, step: GuideStep, league_start: bool, show_optionals: bool) -> bool:
        if "mandatory" in step.tags:
            return True
        if "league_start_only" in step.tags and not league_start:
            return False
        if "optional" in step.tags and not show_optionals:
            return False
        return True

    def advance(self):
        if not self.current_step_id:
            return
        current = self.steps[self.current_step_id]
        if current.next_steps:
            self.current_step_id = current.next_steps[0]
        else:
            candidates = [
                sid for sid, step in self.steps.items()
                if step.step_number > current.step_number and step.act == current.act
            ]
            if candidates:
                self.current_step_id = min(candidates, key=lambda k: self.steps[k].step_number)

    def retreat(self):
        if not self.current_step_id:
            return
        current = self.steps[self.current_step_id]
        candidates = [
            sid for sid, step in self.steps.items()
            if self.current_step_id in step.next_steps
        ]
        if candidates:
            self.current_step_id = min(candidates, key=lambda k: self.steps[k].step_number)
        else:
            candidates = [
                sid for sid, step in self.steps.items()
                if step.step_number < current.step_number and step.act == current.act
            ]
            if candidates:
                self.current_step_id = max(candidates, key=lambda k: self.steps[k].step_number)

    def handle_zone_enter(self, zone: str):
        if not self.current_step_id:
            return
        self.current_zone = zone
        current = self.steps[self.current_step_id]
        logger.debug(f"Zone enter: '{zone}' | current_step: {current.id} (step_number={current.step_number}, zone='{current.zone}')")

        if current.auto_advance_trigger:
            trigger = current.auto_advance_trigger
            if trigger.get("type") == "enter_area":
                if trigger.get("target_area", "") == zone:
                    logger.debug("Phase 1 match: current step trigger -> advance()")
                    self.advance()
                    return
                else:
                    logger.debug(f"Phase 1 mismatch: trigger target='{trigger.get('target_area','')}' != zone='{zone}'")

        for sid, step in self.steps.items():
            if step.auto_advance_trigger:
                trigger = step.auto_advance_trigger
                if trigger.get("type") == "enter_area":
                    if trigger.get("target_area", "") == zone:
                        logger.debug(f"Phase 2 match: step {sid} trigger -> jump to {sid}")
                        self.current_step_id = sid
                        return

        if current.zone != zone:
            candidates = [
                sid for sid, step in sorted(self.steps.items(), key=lambda x: x[1].step_number)
                if step.zone == zone and step.step_number > current.step_number
            ]
            logger.debug(f"Phase 3 fallback: current.zone='{current.zone}' != zone='{zone}', candidates={candidates}")
            if candidates:
                self.current_step_id = candidates[0]
                logger.debug(f"Phase 3 -> jumped to {candidates[0]}")
                return

        logger.debug(f"No advancement for zone='{zone}'")

    def reset(self):
        if self.steps:
            self.current_step_id = min(self.steps.keys(), key=lambda k: self.steps[k].step_number)

    def get_zone_reward(self, zone: str) -> str:
        from sin_guide.data.zone_rewards import ZONE_LEAGUE_REWARDS
        return ZONE_LEAGUE_REWARDS.get(zone, "")
