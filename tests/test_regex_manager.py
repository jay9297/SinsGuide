"""Tests for RegexEntry validation and RegexManager CRUD / navigation."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from sin_guide.config.manager import ConfigManager
from sin_guide.core.regex_manager import (
    RegexEntry,
    RegexIndexError,
    RegexManager,
    RegexValidationError,
    MAX_NAME_LENGTH,
    MAX_PATTERN_LENGTH,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_manager(tmp_path: Path) -> RegexManager:
    """Construct a RegexManager whose ConfigManager home dir is redirected."""
    with patch("sin_guide.config.manager.Path.home", return_value=tmp_path):
        config = ConfigManager()
    return RegexManager(config)


def make_entry(name: str = "Maps", pattern: str = "map") -> RegexEntry:
    """Create a simple valid RegexEntry for test setup."""
    return RegexEntry.create(name, pattern)


# ---------------------------------------------------------------------------
# RegexEntry
# ---------------------------------------------------------------------------


class TestRegexEntryCreate:
    """Tests for RegexEntry.create() factory + validation."""

    def test_create_valid_entry(self) -> None:
        entry = RegexEntry.create("Maps", "map")
        assert entry.name == "Maps"
        assert entry.pattern == "map"
        assert isinstance(entry.created_at, str)
        # created_at should be a valid ISO-8601 timestamp
        from datetime import datetime

        parsed = datetime.fromisoformat(entry.created_at)
        assert parsed.tzinfo is not None  # UTC timezone

    def test_create_rejects_empty_name(self) -> None:
        with pytest.raises(RegexValidationError, match="must be non-empty"):
            RegexEntry.create("", "map")

    def test_create_rejects_whitespace_only_name(self) -> None:
        with pytest.raises(RegexValidationError, match="must be non-empty"):
            RegexEntry.create("   ", "map")

    def test_create_rejects_long_name(self) -> None:
        too_long = "x" * (MAX_NAME_LENGTH + 1)
        with pytest.raises(RegexValidationError, match=f"exceeds {MAX_NAME_LENGTH}"):
            RegexEntry.create(too_long, "map")

    def test_create_allows_name_at_max_length(self) -> None:
        at_max = "x" * MAX_NAME_LENGTH
        entry = RegexEntry.create(at_max, "map")
        assert len(entry.name) == MAX_NAME_LENGTH

    def test_create_rejects_empty_pattern(self) -> None:
        with pytest.raises(RegexValidationError, match="must be non-empty"):
            RegexEntry.create("Maps", "")

    def test_create_rejects_whitespace_only_pattern(self) -> None:
        with pytest.raises(RegexValidationError, match="must be non-empty"):
            RegexEntry.create("Maps", "   ")

    def test_create_rejects_long_pattern(self) -> None:
        too_long = "x" * (MAX_PATTERN_LENGTH + 1)
        with pytest.raises(RegexValidationError, match=f"exceeds {MAX_PATTERN_LENGTH}"):
            RegexEntry.create("Maps", too_long)

    def test_create_allows_pattern_at_max_length(self) -> None:
        at_max = "x" * MAX_PATTERN_LENGTH
        entry = RegexEntry.create("Maps", at_max)
        assert len(entry.pattern) == MAX_PATTERN_LENGTH

    def test_create_strips_whitespace(self) -> None:
        entry = RegexEntry.create("  Maps  ", "  map  ")
        assert entry.name == "Maps"
        assert entry.pattern == "map"


class TestRegexEntrySerialisation:
    """Tests for RegexEntry.to_dict() / from_dict() round-trip."""

    def test_to_dict(self) -> None:
        entry = RegexEntry.create("Maps", "map")
        d = entry.to_dict()
        assert d["name"] == "Maps"
        assert d["pattern"] == "map"
        assert "created_at" in d

    def test_from_dict(self) -> None:
        data = {"name": "Essences", "pattern": "essence", "created_at": "2024-01-01T00:00:00+00:00"}
        entry = RegexEntry.from_dict(data)
        assert entry.name == "Essences"
        assert entry.pattern == "essence"
        assert entry.created_at == "2024-01-01T00:00:00+00:00"

    def test_to_dict_from_dict_roundtrip(self) -> None:
        original = RegexEntry.create("Maps", "map")
        restored = RegexEntry.from_dict(original.to_dict())
        assert restored.name == original.name
        assert restored.pattern == original.pattern
        assert restored.created_at == original.created_at

    def test_immutability(self) -> None:
        """RegexEntry is a frozen dataclass — cannot modify after creation."""
        entry = RegexEntry.create("Maps", "map")
        with pytest.raises(Exception):
            entry.name = "Changed"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# RegexManager — CRUD
# ---------------------------------------------------------------------------


class TestRegexManagerCRUD:
    """Tests for add, remove, update, get_entry, list_entries."""

    def test_add_entry(self, tmp_path: Path) -> None:
        manager = make_manager(tmp_path)
        entry = manager.add_entry("Maps", "map")
        assert entry.name == "Maps"
        assert entry.pattern == "map"
        assert manager.count == 1
        assert manager.list_entries() == [entry]

    def test_add_entry_raises_on_invalid_name(self, tmp_path: Path) -> None:
        manager = make_manager(tmp_path)
        with pytest.raises(RegexValidationError):
            manager.add_entry("", "map")

    def test_add_entry_raises_on_invalid_pattern(self, tmp_path: Path) -> None:
        manager = make_manager(tmp_path)
        with pytest.raises(RegexValidationError):
            manager.add_entry("Maps", "")

    def test_remove_entry(self, tmp_path: Path) -> None:
        manager = make_manager(tmp_path)
        manager.add_entry("Maps", "map")
        manager.add_entry("Essences", "essence")

        removed = manager.remove_entry(0)
        assert removed.name == "Maps"
        assert manager.count == 1
        assert manager.get_entry(0).name == "Essences"

    def test_remove_entry_at_last_index(self, tmp_path: Path) -> None:
        manager = make_manager(tmp_path)
        manager.add_entry("Maps", "map")
        manager.add_entry("Essences", "essence")

        removed = manager.remove_entry(1)
        assert removed.name == "Essences"
        assert manager.count == 1

    def test_remove_entry_adjusts_current_index(self, tmp_path: Path) -> None:
        """When removing the current entry, current_index is clamped."""
        manager = make_manager(tmp_path)
        manager.add_entry("A", "a")
        manager.add_entry("B", "b")
        manager.set_current(1)

        manager.remove_entry(1)
        assert manager.current_index == 0
        assert manager.get_current().name == "A"  # type: ignore[union-attr]

    def test_remove_last_entry_clamps_to_zero(self, tmp_path: Path) -> None:
        manager = make_manager(tmp_path)
        manager.add_entry("Only", "only")
        manager.remove_entry(0)
        assert manager.count == 0
        assert manager.current_index == 0

    def test_remove_entry_out_of_bounds(self, tmp_path: Path) -> None:
        manager = make_manager(tmp_path)
        manager.add_entry("Maps", "map")
        with pytest.raises(RegexIndexError, match="out of range"):
            manager.remove_entry(5)

    def test_remove_entry_negative_index(self, tmp_path: Path) -> None:
        manager = make_manager(tmp_path)
        manager.add_entry("Maps", "map")
        with pytest.raises(RegexIndexError, match="non-negative"):
            manager.remove_entry(-1)

    def test_update_entry(self, tmp_path: Path) -> None:
        manager = make_manager(tmp_path)
        manager.add_entry("Maps", "map")
        updated = manager.update_entry(0, "T16 Maps", "tier 16")
        assert updated.name == "T16 Maps"
        assert updated.pattern == "tier 16"
        assert manager.count == 1

    def test_update_entry_raises_on_invalid_name(self, tmp_path: Path) -> None:
        manager = make_manager(tmp_path)
        manager.add_entry("Maps", "map")
        with pytest.raises(RegexValidationError):
            manager.update_entry(0, "", "valid")

    def test_update_entry_raises_on_invalid_pattern(self, tmp_path: Path) -> None:
        manager = make_manager(tmp_path)
        manager.add_entry("Maps", "map")
        with pytest.raises(RegexValidationError):
            manager.update_entry(0, "valid", "")

    def test_update_entry_out_of_bounds(self, tmp_path: Path) -> None:
        manager = make_manager(tmp_path)
        with pytest.raises(RegexIndexError):
            manager.update_entry(0, "Maps", "map")

    def test_get_entry(self, tmp_path: Path) -> None:
        manager = make_manager(tmp_path)
        manager.add_entry("Maps", "map")
        entry = manager.get_entry(0)
        assert entry.name == "Maps"
        assert entry.pattern == "map"

    def test_get_entry_out_of_bounds(self, tmp_path: Path) -> None:
        manager = make_manager(tmp_path)
        with pytest.raises(RegexIndexError):
            manager.get_entry(0)

    def test_get_entry_wrong_type(self, tmp_path: Path) -> None:
        manager = make_manager(tmp_path)
        with pytest.raises(TypeError, match="must be an integer"):
            manager.get_entry("not_an_int")  # type: ignore[arg-type]

    def test_list_entries_returns_shallow_copy(self, tmp_path: Path) -> None:
        manager = make_manager(tmp_path)
        manager.add_entry("Maps", "map")
        entries = manager.list_entries()
        entries.append(make_entry("Extra"))
        assert manager.count == 1

    def test_list_entries_empty(self, tmp_path: Path) -> None:
        manager = make_manager(tmp_path)
        assert manager.list_entries() == []

    def test_add_multiple_entries(self, tmp_path: Path) -> None:
        manager = make_manager(tmp_path)
        manager.add_entry("A", "a")
        manager.add_entry("B", "b")
        manager.add_entry("C", "c")
        assert manager.count == 3
        names = [e.name for e in manager.list_entries()]
        assert names == ["A", "B", "C"]


# ---------------------------------------------------------------------------
# RegexManager — Navigation / cycling
# ---------------------------------------------------------------------------


class TestRegexManagerNavigation:
    """Tests for get_current, next_regex, prev_regex, set_current."""

    def test_get_current_returns_first_by_default(self, tmp_path: Path) -> None:
        manager = make_manager(tmp_path)
        manager.add_entry("A", "a")
        manager.add_entry("B", "b")
        current = manager.get_current()
        assert current is not None
        assert current.name == "A"

    def test_get_current_returns_none_when_empty(self, tmp_path: Path) -> None:
        manager = make_manager(tmp_path)
        assert manager.get_current() is None

    def test_next_regex_advances(self, tmp_path: Path) -> None:
        manager = make_manager(tmp_path)
        manager.add_entry("A", "a")
        manager.add_entry("B", "b")
        manager.add_entry("C", "c")

        entry = manager.next_regex()
        assert entry.name == "B"
        assert manager.current_index == 1

    def test_next_regex_wraps_around(self, tmp_path: Path) -> None:
        manager = make_manager(tmp_path)
        manager.add_entry("A", "a")
        manager.add_entry("B", "b")

        manager.next_regex()
        entry = manager.next_regex()
        assert entry.name == "A"
        assert manager.current_index == 0

    def test_next_regex_returns_none_when_empty(self, tmp_path: Path) -> None:
        manager = make_manager(tmp_path)
        assert manager.next_regex() is None

    def test_prev_regex_goes_backward(self, tmp_path: Path) -> None:
        manager = make_manager(tmp_path)
        manager.add_entry("A", "a")
        manager.add_entry("B", "b")
        manager.add_entry("C", "c")

        entry = manager.prev_regex()
        assert entry.name == "C"
        assert manager.current_index == 2

    def test_prev_regex_wraps_from_zero(self, tmp_path: Path) -> None:
        manager = make_manager(tmp_path)
        manager.add_entry("A", "a")
        manager.add_entry("B", "b")

        entry = manager.prev_regex()
        assert entry.name == "B"
        assert manager.current_index == 1

    def test_prev_regex_returns_none_when_empty(self, tmp_path: Path) -> None:
        manager = make_manager(tmp_path)
        assert manager.prev_regex() is None

    def test_set_current(self, tmp_path: Path) -> None:
        manager = make_manager(tmp_path)
        manager.add_entry("A", "a")
        manager.add_entry("B", "b")
        manager.add_entry("C", "c")

        entry = manager.set_current(2)
        assert entry.name == "C"
        assert manager.current_index == 2

    def test_set_current_out_of_bounds(self, tmp_path: Path) -> None:
        manager = make_manager(tmp_path)
        manager.add_entry("Maps", "map")
        with pytest.raises(RegexIndexError):
            manager.set_current(5)

    def test_set_current_negative(self, tmp_path: Path) -> None:
        manager = make_manager(tmp_path)
        manager.add_entry("Maps", "map")
        with pytest.raises(RegexIndexError):
            manager.set_current(-1)

    def test_next_regex_persists_index(self, tmp_path: Path) -> None:
        """Cycling with next_regex saves the current_index to config."""
        manager = make_manager(tmp_path)
        manager.add_entry("A", "a")
        manager.add_entry("B", "b")
        manager.next_regex()

        manager2 = make_manager(tmp_path)
        assert manager2.current_index == 1
        current = manager2.get_current()
        assert current is not None
        assert current.name == "B"

    def test_prev_regex_persists_index(self, tmp_path: Path) -> None:
        """Cycling with prev_regex saves the current_index to config."""
        manager = make_manager(tmp_path)
        manager.add_entry("A", "a")
        manager.add_entry("B", "b")
        manager.prev_regex()

        manager2 = make_manager(tmp_path)
        assert manager2.current_index == 1

    def test_set_current_persists_index(self, tmp_path: Path) -> None:
        manager = make_manager(tmp_path)
        manager.add_entry("A", "a")
        manager.add_entry("B", "b")
        manager.add_entry("C", "c")
        manager.set_current(2)

        manager2 = make_manager(tmp_path)
        assert manager2.current_index == 2


# ---------------------------------------------------------------------------
# RegexManager — Count / current_index
# ---------------------------------------------------------------------------


class TestRegexManagerProperties:
    """Tests for count and current_index properties."""

    def test_count_zero_initially(self, tmp_path: Path) -> None:
        manager = make_manager(tmp_path)
        assert manager.count == 0

    def test_count_reflects_entries(self, tmp_path: Path) -> None:
        manager = make_manager(tmp_path)
        manager.add_entry("A", "a")
        assert manager.count == 1
        manager.add_entry("B", "b")
        assert manager.count == 2
        manager.remove_entry(0)
        assert manager.count == 1

    def test_current_index_zero_initially(self, tmp_path: Path) -> None:
        manager = make_manager(tmp_path)
        assert manager.current_index == 0

    def test_current_index_clamped_on_load(self, tmp_path: Path) -> None:
        """If config has an out-of-range index, it is clamped on load."""
        with patch("sin_guide.config.manager.Path.home", return_value=tmp_path):
            config = ConfigManager()
            config.set("regexes.entries", [])
            config.set("regexes.current_index", 99)

        manager = RegexManager(config)
        assert manager.current_index == 0


# ---------------------------------------------------------------------------
# RegexManager — Empty list behaviour
# ---------------------------------------------------------------------------


class TestRegexManagerEmpty:
    """Tests for behaviour when the manager has zero entries."""

    def test_empty_list_get_current_returns_none(self, tmp_path: Path) -> None:
        manager = make_manager(tmp_path)
        assert manager.get_current() is None

    def test_empty_list_next_regex_returns_none(self, tmp_path: Path) -> None:
        manager = make_manager(tmp_path)
        assert manager.next_regex() is None

    def test_empty_list_prev_regex_returns_none(self, tmp_path: Path) -> None:
        manager = make_manager(tmp_path)
        assert manager.prev_regex() is None

    def test_empty_list_get_entry_raises(self, tmp_path: Path) -> None:
        manager = make_manager(tmp_path)
        with pytest.raises(RegexIndexError):
            manager.get_entry(0)

    def test_empty_list_remove_entry_raises(self, tmp_path: Path) -> None:
        manager = make_manager(tmp_path)
        with pytest.raises(RegexIndexError):
            manager.remove_entry(0)

    def test_empty_list_count_zero(self, tmp_path: Path) -> None:
        manager = make_manager(tmp_path)
        assert manager.count == 0

    def test_empty_list_list_entries_empty(self, tmp_path: Path) -> None:
        manager = make_manager(tmp_path)
        assert manager.list_entries() == []


# ---------------------------------------------------------------------------
# RegexManager — Persistence round-trips
# ---------------------------------------------------------------------------


class TestRegexManagerPersistence:
    """Tests that entry data survives save/load cycles."""

    def test_persistence_roundtrip(self, tmp_path: Path) -> None:
        """Add entries, create a new manager, verify they load back."""
        manager1 = make_manager(tmp_path)
        manager1.add_entry("Maps", "map")
        manager1.add_entry("Essences", "essence")
        assert manager1.count == 2

        manager2 = make_manager(tmp_path)
        assert manager2.count == 2
        assert manager2.get_entry(0).name == "Maps"
        assert manager2.get_entry(1).name == "Essences"

    def test_persistence_with_remove(self, tmp_path: Path) -> None:
        manager1 = make_manager(tmp_path)
        manager1.add_entry("A", "a")
        manager1.add_entry("B", "b")
        manager1.add_entry("C", "c")
        manager1.remove_entry(1)

        manager2 = make_manager(tmp_path)
        assert manager2.count == 2
        assert manager2.get_entry(0).name == "A"
        assert manager2.get_entry(1).name == "C"

    def test_persistence_with_update(self, tmp_path: Path) -> None:
        manager1 = make_manager(tmp_path)
        manager1.add_entry("Original", "orig")
        manager1.update_entry(0, "Updated", "upd")

        manager2 = make_manager(tmp_path)
        assert manager2.get_entry(0).name == "Updated"
        assert manager2.get_entry(0).pattern == "upd"

    def test_persistence_preserves_created_at(self, tmp_path: Path) -> None:
        manager1 = make_manager(tmp_path)
        entry1 = manager1.add_entry("Maps", "map")
        original_timestamp = entry1.created_at

        manager2 = make_manager(tmp_path)
        loaded_entry = manager2.get_entry(0)
        assert loaded_entry.created_at == original_timestamp

    def test_persistence_empty_collection(self, tmp_path: Path) -> None:
        """A fresh manager created after no data was saved starts empty."""
        make_manager(tmp_path)  # establish config file without adding entries

        manager2 = make_manager(tmp_path)
        assert manager2.count == 0
        assert manager2.list_entries() == []
