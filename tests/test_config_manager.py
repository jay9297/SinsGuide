"""Tests for ConfigManager — config loading, merging, get/set, reload."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from sin_guide.config.defaults import DEFAULT_CONFIG
from sin_guide.config.manager import ConfigManager


def make_manager(tmp_path: Path) -> ConfigManager:
    """Construct a ConfigManager whose home dir is redirected to tmp_path."""
    with patch("sin_guide.config.manager.Path.home", return_value=tmp_path):
        return ConfigManager()


class TestLoadMissingFile:
    def test_creates_defaults_when_no_file(self, tmp_path: Path) -> None:
        # Arrange / Act
        make_manager(tmp_path)

        # Assert — config.json was written
        config_file = tmp_path / ".config" / "sin_guide" / "config.json"
        assert config_file.exists()

    def test_default_values_are_loaded(self, tmp_path: Path) -> None:
        # Arrange / Act
        manager = make_manager(tmp_path)

        # Assert
        assert manager.get("overlay.transparency") == DEFAULT_CONFIG["overlay"]["transparency"]
        assert manager.get("overlay.font_size") == DEFAULT_CONFIG["overlay"]["font_size"]
        assert manager.get("guide.league_start") == DEFAULT_CONFIG["guide"]["league_start"]

    def test_all_returns_dict(self, tmp_path: Path) -> None:
        manager = make_manager(tmp_path)
        result = manager.all()
        assert isinstance(result, dict)
        assert "overlay" in result
        assert "guide" in result


class TestLoadValidJson:
    def test_loads_existing_json(self, tmp_path: Path) -> None:
        # Arrange — write a valid config file first
        config_dir = tmp_path / ".config" / "sin_guide"
        config_dir.mkdir(parents=True)
        config_file = config_dir / "config.json"
        custom = {"overlay": {"transparency": 0.5, "font_size": 16}}
        config_file.write_text(json.dumps(custom))

        # Act
        manager = make_manager(tmp_path)

        # Assert — custom values override defaults
        assert manager.get("overlay.transparency") == 0.5
        assert manager.get("overlay.font_size") == 16

    def test_missing_keys_fall_back_to_defaults(self, tmp_path: Path) -> None:
        # Arrange — partial config (only overlay section, no guide)
        config_dir = tmp_path / ".config" / "sin_guide"
        config_dir.mkdir(parents=True)
        config_file = config_dir / "config.json"
        config_file.write_text(json.dumps({"overlay": {"transparency": 0.9}}))

        # Act
        manager = make_manager(tmp_path)

        # Assert — guide section still has defaults
        assert manager.get("guide.league_start") == DEFAULT_CONFIG["guide"]["league_start"]


class TestLoadCorruptedJson:
    def test_corrupted_json_triggers_backup(self, tmp_path: Path) -> None:
        # Arrange
        config_dir = tmp_path / ".config" / "sin_guide"
        config_dir.mkdir(parents=True)
        config_file = config_dir / "config.json"
        config_file.write_text("{ this is not valid json !!!")

        # Act
        make_manager(tmp_path)

        # Assert — backup file was created
        backup = config_dir / "config.json.bak"
        assert backup.exists()

    def test_corrupted_json_loads_defaults(self, tmp_path: Path) -> None:
        # Arrange
        config_dir = tmp_path / ".config" / "sin_guide"
        config_dir.mkdir(parents=True)
        config_file = config_dir / "config.json"
        config_file.write_text("not json at all")

        # Act
        manager = make_manager(tmp_path)

        # Assert — in-memory config is defaults
        assert manager.get("overlay.transparency") == DEFAULT_CONFIG["overlay"]["transparency"]


class TestGetDottedKeys:
    def test_simple_dotted_key(self, tmp_path: Path) -> None:
        manager = make_manager(tmp_path)
        assert manager.get("overlay.show_timer") == DEFAULT_CONFIG["overlay"]["show_timer"]

    def test_nested_dotted_key(self, tmp_path: Path) -> None:
        manager = make_manager(tmp_path)
        assert manager.get("hotkeys.prev_step") == DEFAULT_CONFIG["hotkeys"]["prev_step"]

    def test_missing_key_returns_default(self, tmp_path: Path) -> None:
        manager = make_manager(tmp_path)
        assert manager.get("nonexistent.key", "fallback") == "fallback"

    def test_missing_key_returns_none_by_default(self, tmp_path: Path) -> None:
        manager = make_manager(tmp_path)
        assert manager.get("does.not.exist") is None

    def test_top_level_key(self, tmp_path: Path) -> None:
        manager = make_manager(tmp_path)
        result = manager.get("overlay")
        assert isinstance(result, dict)
        assert "transparency" in result


class TestSet:
    def test_set_persists_to_disk(self, tmp_path: Path) -> None:
        # Arrange
        manager = make_manager(tmp_path)

        # Act
        manager.set("overlay.transparency", 0.42)

        # Assert — read file back directly
        config_file = tmp_path / ".config" / "sin_guide" / "config.json"
        data = json.loads(config_file.read_text())
        assert data["overlay"]["transparency"] == pytest.approx(0.42)

    def test_set_updates_in_memory(self, tmp_path: Path) -> None:
        manager = make_manager(tmp_path)
        manager.set("overlay.font_size", 18)
        assert manager.get("overlay.font_size") == 18

    def test_set_creates_nested_key(self, tmp_path: Path) -> None:
        manager = make_manager(tmp_path)
        manager.set("newgroup.newkey", "hello")
        assert manager.get("newgroup.newkey") == "hello"

    def test_set_string_value(self, tmp_path: Path) -> None:
        manager = make_manager(tmp_path)
        manager.set("guide.character_name", "Wraeclast")
        assert manager.get("guide.character_name") == "Wraeclast"

    def test_set_boolean_value(self, tmp_path: Path) -> None:
        manager = make_manager(tmp_path)
        manager.set("overlay.show_timer", False)
        assert manager.get("overlay.show_timer") is False


class TestMergeDefaults:
    def test_nested_merge_preserves_user_values(self, tmp_path: Path) -> None:
        # Arrange — user file has only one overlay key
        config_dir = tmp_path / ".config" / "sin_guide"
        config_dir.mkdir(parents=True)
        config_file = config_dir / "config.json"
        config_file.write_text(json.dumps({"overlay": {"transparency": 0.3}}))

        # Act
        manager = make_manager(tmp_path)

        # Assert — user value kept, other overlay keys filled from defaults
        assert manager.get("overlay.transparency") == pytest.approx(0.3)
        assert manager.get("overlay.font_size") == DEFAULT_CONFIG["overlay"]["font_size"]

    def test_unrecognised_top_level_key_not_merged(self, tmp_path: Path) -> None:
        config_dir = tmp_path / ".config" / "sin_guide"
        config_dir.mkdir(parents=True)
        config_file = config_dir / "config.json"
        config_file.write_text(json.dumps({"totally_unknown": {"x": 1}}))

        manager = make_manager(tmp_path)

        # Unknown top-level keys that are not in DEFAULT_CONFIG are dropped
        assert manager.get("totally_unknown.x") is None


class TestReload:
    def test_reload_picks_up_external_changes(self, tmp_path: Path) -> None:
        # Arrange
        manager = make_manager(tmp_path)
        config_file = tmp_path / ".config" / "sin_guide" / "config.json"

        # Externally modify the file
        data = json.loads(config_file.read_text())
        data["overlay"]["font_size"] = 22
        config_file.write_text(json.dumps(data))

        # Act
        manager.reload()

        # Assert
        assert manager.get("overlay.font_size") == 22

    def test_reload_does_not_duplicate_csv_or_crash(self, tmp_path: Path) -> None:
        manager = make_manager(tmp_path)
        # Should not raise
        manager.reload()
        manager.reload()
        assert manager.get("overlay.transparency") is not None
