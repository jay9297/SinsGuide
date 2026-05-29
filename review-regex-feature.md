# Code Review: Regex Storage Feature

**Date**: 2026-05-29  
**Branch**: dev  
**Files reviewed**: `main.py`, `sin_guide/config/defaults.py`, `sin_guide/config/manager.py`, `sin_guide/overlay/main_window.py`, `sin_guide/overlay/settings_panel.py`, `sin_guide/core/regex_manager.py`, `sin_guide/overlay/regex_widget.py`, `tests/test_regex_manager.py`

**Decision**: REQUEST CHANGES

---

## Validation Results

| Check | Result |
|---|---|
| Tests (350 total) | PASS |
| mypy | FAIL — 13 errors in 5 files |
| ruff | FAIL — 1 error |

---

## Findings

### HIGH

#### 1. `settings_panel.py` — `_regex_manager` null-dereference not guarded (mypy errors)

**Files**: `sin_guide/overlay/settings_panel.py:238, 248, 256, 266, 277`

`self._regex_manager` is typed `RegexManager | None`. The CRUD methods (`_on_add_regex`, `_on_edit_regex`, `_on_remove_regex`) call methods on it without narrowing away `None`, triggering 5 mypy `union-attr` errors. Although the group box is disabled at the UI level when `_regex_manager is None`, mypy cannot see that, and nothing prevents a future code path from bypassing the guard.

**Fix**: Add an early-return assertion at the top of each method:

```python
def _on_add_regex(self) -> None:
    if self._regex_manager is None:
        return
    ...
```

#### 2. `settings_panel.py` — `str | None` passed where `str` is required (mypy errors)

**Files**: `sin_guide/overlay/settings_panel.py:238, 256`

`_show_regex_dialog` returns `tuple[str | None, str | None]`. Callers do `if name is None: return` but mypy cannot narrow `pattern` to `str` in the same branch. Both `add_entry` and `update_entry` expect `str`, not `str | None`.

**Fix**: Widen the guard or restructure the check:

```python
name, pattern = self._show_regex_dialog(...)
if name is None or pattern is None:
    return
```

---

### MEDIUM

#### 3. `defaults.py` — `hotkeys.regex_copy` config key defined but never read

**File**: `sin_guide/config/defaults.py:20`

```python
"regex_copy": "F6",
```

The F6 key is hardcoded as `"<f6>"` in `main.py:183` (and the listener in `_init_regex_hotkey` constructs the binding directly). The config value is never read, so a user cannot remap F6 via settings. Either wire it up or remove the dead config entry.

#### 4. `settings_panel.py` — dialog-local widgets stored as instance attributes

**File**: `sin_guide/overlay/settings_panel.py:293, 299, 305`

`_show_regex_dialog` assigns `self._regex_name_input`, `self._regex_pattern_input`, and `self._regex_dialog_hint` as instance attributes on `SettingsPanel`. These widgets live only for the duration of the dialog. Storing them on `self` pollutes the object namespace, leaks the last dialog's widgets between calls, and could cause subtle bugs if the panel is reused. They should be local variables.

**Fix**: Replace `self._regex_name_input` with `name_input` (and same for the others) and capture them in the lambda closures directly.

#### 5. `main_window.py` — `DragHandle._drag_pos` is a dead attribute

**File**: `sin_guide/overlay/main_window.py:40, 71`

`_drag_pos` is set to `None` in `__init__` (line 40) and reset to `None` in `mouseReleaseEvent` (line 71) but is never read anywhere — `startSystemMove()` handles the actual dragging. The attribute is dead weight.

**Fix**: Remove the `_drag_pos` attribute entirely from `DragHandle`.

#### 6. `regex_manager.py` — `RegexEntry.from_dict` has no error handling

**File**: `sin_guide/core/regex_manager.py:83–96`

`from_dict` accesses `data["name"]`, `data["pattern"]`, `data["created_at"]` directly. If the config JSON is corrupted or a key is missing (which the existing `_backup_corrupted` path in `ConfigManager` already anticipates), this raises an unhandled `KeyError` inside `RegexManager._load()`, which is called from `__init__`. The exception will propagate uncaught and crash the app startup.

**Fix**: Wrap in a try/except inside `_load()` and skip/discard malformed entries with a warning log, similar to how `ConfigManager._backup_corrupted` handles a broken file:

```python
entries = []
for e in raw_entries:
    try:
        entries.append(RegexEntry.from_dict(e))
    except (KeyError, TypeError):
        logger.warning("Skipping malformed regex entry: %r", e)
self._entries = entries
```

---

### LOW

#### 7. `tests/test_regex_manager.py:517` — unused variable `manager1` (ruff F841)

**File**: `tests/test_regex_manager.py:517`

```python
def test_persistence_empty_collection(self, tmp_path: Path) -> None:
    manager1 = make_manager(tmp_path)  # assigned, never used
    manager2 = make_manager(tmp_path)
    ...
```

The test intent is presumably "a new manager sees an empty collection even after a first manager's empty save". Either add a meaningful operation on `manager1` to make the test non-trivial, or remove `manager1` entirely (the test is equivalent to `test_count_zero_initially` without it).

**Fix (minimal)**: Remove the unused assignment or rename to `_`:
```python
make_manager(tmp_path)  # establish config file
manager2 = make_manager(tmp_path)
```

#### 8. `regex_widget.py:57` — emoji in user-visible label

**File**: `sin_guide/overlay/regex_widget.py:57`

```python
self.setText(f"\U0001F4CB {name}")
```

The project CLAUDE.md and coding-style rules say "Only use emojis if the user explicitly requests it." The clipboard emoji (📋) is hardcoded into the displayed label without it being an explicit user requirement. Remove or replace with plain text.

#### 9. `main.py` / `main_window.py` — f-string logger calls inconsistent with `%s` style

**Files**: `main.py:66, 247`; `sin_guide/overlay/main_window.py:318, 436`

Most log calls in the codebase use `%s` lazy formatting (`logger.error("...: %s", e)`), but a handful use f-strings (`logger.debug(f"Parsed zone enter: '{event.data}'")`). f-strings are evaluated eagerly even when the log level is not active, which wastes CPU. Standardise on `%s`.

#### 10. `main_window.py` — `on_settings_requested` is an untyped duck-typed callback

**File**: `sin_guide/overlay/main_window.py:399`; set in `main.py:126`

```python
self.overlay.on_settings_requested = self.show_settings
```

The attribute is never declared in `OverlayWindow.__init__` and has no type annotation, so mypy cannot check callers. Consider declaring it properly:

```python
# in OverlayWindow.__init__:
self.on_settings_requested: Callable[[], None] | None = None
```

---

## Summary

The regex storage feature is well-structured — `RegexManager` is clean, the test suite is thorough (350 tests all passing), and `RegexEntry` correctly uses a frozen dataclass. The critical fixes needed are the two mypy HIGH issues in `settings_panel.py` (null guards + `str | None` narrowing) which represent real potential bugs. The `from_dict` error handling gap (issue 6) is a low-likelihood but high-impact crash path worth closing before merge. The remaining items are cleanup and consistency improvements.
