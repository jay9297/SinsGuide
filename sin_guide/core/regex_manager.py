"""Regex storage and management for vendor item filtering in Path of Exile 2.

Provides the RegexManager class for managing a collection of filter regexes
that can be used to highlight vendor items. Regexes are persisted via the
ConfigManager in ``~/.config/sin_guide/config.json`` under the ``"regexes"`` key.

PoE2 imposes a hard 250-character limit on stash tab filter patterns, enforced
by this module's validation.
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

from sin_guide.config.manager import ConfigManager

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CONFIG_KEY_ENTRIES = "regexes.entries"
CONFIG_KEY_CURRENT_INDEX = "regexes.current_index"
MAX_PATTERN_LENGTH = 250
MAX_NAME_LENGTH = 50
DEFAULT_REGEXES: list[dict[str, str]] = []


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class RegexValidationError(ValueError):
    """Raised when a regex entry fails validation (name/pattern constraints)."""


class RegexIndexError(IndexError):
    """Raised when a regex index is out of bounds."""


# ---------------------------------------------------------------------------
# RegexEntry
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RegexEntry:
    """Immutable representation of a single vendor-item filter regex.

    Attributes:
        name: Human-readable label for the regex (e.g. "Maps").
        pattern: The PoE2 stash-tab filter pattern string.
        created_at: UTC ISO-8601 timestamp of when the entry was created.
    """

    name: str
    pattern: str
    created_at: str

    @classmethod
    def create(cls, name: str, pattern: str) -> RegexEntry:
        """Factory that validates and creates a new entry with a UTC timestamp.

        Args:
            name: Human-readable label (1–50 chars, non-empty).
            pattern: PoE2 filter pattern string (1–250 chars, non-empty).

        Returns:
            A new validated ``RegexEntry``.

        Raises:
            RegexValidationError: If *name* or *pattern* fail validation.
        """
        cls._validate(name, pattern)
        created_at = datetime.now(tz=timezone.utc).isoformat()
        return cls(name=name.strip(), pattern=pattern.strip(), created_at=created_at)

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> RegexEntry:
        """Construct a ``RegexEntry`` from a plain dict (e.g. loaded from config).

        Args:
            data: Dict with ``name``, ``pattern``, and ``created_at`` keys.

        Returns:
            A ``RegexEntry`` instance.
        """
        return cls(
            name=data["name"],
            pattern=data["pattern"],
            created_at=data["created_at"],
        )

    def to_dict(self) -> dict[str, str]:
        """Serialize the entry to a plain dict suitable for JSON storage."""
        return asdict(self)

    @staticmethod
    def _validate(name: str, pattern: str) -> None:
        """Validate name and pattern constraints.

        Raises:
            RegexValidationError: On any constraint violation.
        """
        if not name or not name.strip():
            raise RegexValidationError("Regex name must be non-empty.")

        if len(name) > MAX_NAME_LENGTH:
            raise RegexValidationError(
                f"Regex name exceeds {MAX_NAME_LENGTH} characters "
                f"(got {len(name)})."
            )

        if not pattern or not pattern.strip():
            raise RegexValidationError("Regex pattern must be non-empty.")

        if len(pattern) > MAX_PATTERN_LENGTH:
            raise RegexValidationError(
                f"Regex pattern exceeds {MAX_PATTERN_LENGTH} characters "
                f"(got {len(pattern)})."
            )


# ---------------------------------------------------------------------------
# RegexManager
# ---------------------------------------------------------------------------


class RegexManager:
    """Manages a collection of vendor-item filter regexes with persistence.

    Integrates with ``ConfigManager`` to load/save entries under the
    ``"regexes"`` config key. Supports full CRUD operations and cycling
    through entries with wrap-around.

    Args:
        config: The application ``ConfigManager`` instance.
    """

    def __init__(self, config: ConfigManager) -> None:
        self._config = config
        self._entries: list[RegexEntry] = []
        self._current_index: int = 0
        self._load()

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _load(self) -> None:
        """Load regex entries and current index from the config."""
        raw_entries: list[dict[str, Any]] = self._config.get(
            CONFIG_KEY_ENTRIES, DEFAULT_REGEXES
        )
        entries: list[RegexEntry] = []
        for raw in raw_entries:
            try:
                entries.append(RegexEntry.from_dict(raw))
            except (KeyError, TypeError):
                logger.warning("Skipping malformed regex entry: %r", raw)
        self._entries = entries

        raw_index: int = self._config.get(CONFIG_KEY_CURRENT_INDEX, 0)
        self._current_index = self._clamp_index(raw_index)

        logger.debug(
            "Loaded %d regex entries (current_index=%d).",
            len(self._entries),
            self._current_index,
        )

    def _save(self) -> None:
        """Persist all entries and the current index to the config."""
        raw: list[dict[str, str]] = [e.to_dict() for e in self._entries]
        self._config.set(CONFIG_KEY_ENTRIES, raw)
        self._config.set(CONFIG_KEY_CURRENT_INDEX, self._current_index)
        logger.debug(
            "Saved %d regex entries (current_index=%d).",
            len(self._entries),
            self._current_index,
        )

    def _clamp_index(self, value: int) -> int:
        """Clamp *value* to a valid index (0..count-1) or 0 if empty."""
        if not self._entries:
            return 0
        return max(0, min(value, len(self._entries) - 1))

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def add_entry(self, name: str, pattern: str) -> RegexEntry:
        """Add a new regex entry and persist.

        Args:
            name: Human-readable label (1–50 chars, non-empty).
            pattern: PoE2 filter pattern string (1–250 chars, non-empty).

        Returns:
            The newly created ``RegexEntry``.

        Raises:
            RegexValidationError: If *name* or *pattern* fail validation.
        """
        entry = RegexEntry.create(name, pattern)
        self._entries.append(entry)
        self._save()
        logger.info("Added regex entry '%s'.", entry.name)
        return entry

    def remove_entry(self, index: int) -> RegexEntry:
        """Remove a regex entry at *index* and persist.

        Args:
            index: Zero-based index of the entry to remove.

        Returns:
            The removed ``RegexEntry``.

        Raises:
            RegexIndexError: If *index* is out of bounds.
        """
        self._validate_index(index)
        removed = self._entries.pop(index)
        self._current_index = self._clamp_index(self._current_index)
        self._save()
        logger.info("Removed regex entry '%s' at index %d.", removed.name, index)
        return removed

    def update_entry(self, index: int, name: str, pattern: str) -> RegexEntry:
        """Update an existing regex entry and persist.

        Args:
            index: Zero-based index of the entry to update.
            name: New human-readable label (1–50 chars, non-empty).
            pattern: New PoE2 filter pattern string (1–250 chars, non-empty).

        Returns:
            The newly replaced ``RegexEntry``.

        Raises:
            RegexIndexError: If *index* is out of bounds.
            RegexValidationError: If *name* or *pattern* fail validation.
        """
        self._validate_index(index)
        entry = RegexEntry.create(name, pattern)
        old = self._entries[index]
        self._entries[index] = entry
        self._save()
        logger.info("Updated regex entry at index %d: '%s' -> '%s'.", index, old.name, entry.name)
        return entry

    def get_entry(self, index: int) -> RegexEntry:
        """Retrieve the regex entry at *index*.

        Args:
            index: Zero-based index of the entry.

        Returns:
            The ``RegexEntry`` at *index*.

        Raises:
            RegexIndexError: If *index* is out of bounds.
        """
        self._validate_index(index)
        return self._entries[index]

    def list_entries(self) -> list[RegexEntry]:
        """Return a shallow copy of all regex entries."""
        return list(self._entries)

    # ------------------------------------------------------------------
    # Navigation / cycling
    # ------------------------------------------------------------------

    def get_current(self) -> RegexEntry | None:
        """Return the currently selected regex entry, or ``None`` if empty."""
        if not self._entries:
            return None
        return self._entries[self._current_index]

    def next_regex(self) -> RegexEntry | None:
        """Advance to the next entry with wrap-around. Returns the new current.

        If the collection is empty, returns ``None``.
        """
        if not self._entries:
            return None
        self._current_index = (self._current_index + 1) % len(self._entries)
        self._config.set(CONFIG_KEY_CURRENT_INDEX, self._current_index)
        logger.debug("Cycled to next regex: index=%d.", self._current_index)
        return self._entries[self._current_index]

    def prev_regex(self) -> RegexEntry | None:
        """Go back to the previous entry with wrap-around. Returns the new current.

        If the collection is empty, returns ``None``.
        """
        if not self._entries:
            return None
        self._current_index = (self._current_index - 1) % len(self._entries)
        self._config.set(CONFIG_KEY_CURRENT_INDEX, self._current_index)
        logger.debug("Cycled to previous regex: index=%d.", self._current_index)
        return self._entries[self._current_index]

    def set_current(self, index: int) -> RegexEntry:
        """Set the current active entry by *index*.

        Args:
            index: Zero-based index to make current.

        Returns:
            The ``RegexEntry`` now set as current.

        Raises:
            RegexIndexError: If *index* is out of bounds.
        """
        self._validate_index(index)
        self._current_index = index
        self._config.set(CONFIG_KEY_CURRENT_INDEX, self._current_index)
        logger.debug("Set current regex index to %d.", index)
        return self._entries[self._current_index]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @property
    def count(self) -> int:
        """Number of stored regex entries."""
        return len(self._entries)

    @property
    def current_index(self) -> int:
        """Zero-based index of the currently selected entry."""
        return self._current_index

    def _validate_index(self, index: int) -> None:
        """Validate that *index* is a valid non-negative integer within bounds.

        Raises:
            RegexIndexError: If *index* is out of bounds.
            TypeError: If *index* is not an integer.
        """
        if not isinstance(index, int):
            raise TypeError(f"Index must be an integer, got {type(index).__name__}.")

        if index < 0:
            raise RegexIndexError(f"Index must be non-negative, got {index}.")

        if index >= len(self._entries):
            raise RegexIndexError(
                f"Index {index} out of range (collection has {len(self._entries)} entries)."
            )
