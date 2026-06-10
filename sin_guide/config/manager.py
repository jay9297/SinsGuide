import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from .defaults import DEFAULT_CONFIG


class ConfigManager:
    def __init__(self):
        self.config_dir = Path.home() / ".config" / "sin_guide"
        self.config_file = self.config_dir / "config.json"
        self._config: dict[str, Any] = {}
        self._load()

    def _load(self):
        self.config_dir.mkdir(parents=True, exist_ok=True)
        if self.config_file.exists():
            try:
                with open(self.config_file, "r") as f:
                    loaded = json.load(f)
                self._config = self._merge_defaults(loaded)
            except (json.JSONDecodeError, OSError):
                self._backup_corrupted()
                self._config = deepcopy(DEFAULT_CONFIG)
        else:
            self._config = deepcopy(DEFAULT_CONFIG)
            self._save()

    def _merge_defaults(self, loaded: dict) -> dict:
        merged = deepcopy(DEFAULT_CONFIG)
        for key, value in merged.items():
            if isinstance(value, dict) and key in loaded:
                merged[key] = {**value, **loaded[key]}
            elif key in loaded:
                merged[key] = loaded[key]
        return merged

    def _backup_corrupted(self):
        backup = self.config_file.with_suffix(".json.bak")
        try:
            self.config_file.rename(backup)
        except OSError:
            pass

    def _save(self):
        with open(self.config_file, "w") as f:
            json.dump(self._config, f, indent=2)

    def get(self, key: str, default: Any = None) -> Any:
        keys = key.split(".")
        value = self._config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    def set(self, key: str, value: Any):
        keys = key.split(".")
        target = self._config
        for k in keys[:-1]:
            if k not in target:
                target[k] = {}
            target = target[k]
        target[keys[-1]] = value
        self._save()

    def all(self) -> dict[str, Any]:
        return self._config.copy()

    def reload(self):
        self._load()
