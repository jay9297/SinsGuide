# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Sin's Guide is a Path of Exile 2 campaign tracker overlay for Linux — a Python 3.12 / PySide6 port of Lailloken's Exile-UI Act Tracker (originally AHK/Windows). It renders a transparent overlay over the game window (Steam/Proton), tracks campaign progress by tailing PoE2's `Client.txt`, and tracks build gems via OCR.

## Critical rules

1. **The overlay must remain a transparent, click-through Qt window on X11.**
   Do not switch UI frameworks. Do not rewrite the window-tracker module to use
   Wayland-only APIs without explicit approval — XWayland compatibility is the
   product's reason for existing.

2. **OCR is brittle.** Changes to `sin_guide/core/gem_ocr.py` MUST be paired with
   updated test fixtures in `tests/test_gem_ocr.py`. Capture real screenshots
   from PoE2 if changing preprocessing.

3. **Steam Proton prefix discovery must stay robust.** `sin_guide/utils/steam_discovery.py`
   handles a long-tail of weird Steam library configurations. Don't simplify it
   without adding test cases for each variant.

4. **Tests must keep passing at 100%.** The README states "100/100 tests passing."
   That is the floor. PRs that drop the test pass rate are rejected by CI.

5. **No mutable global state in the overlay.** All settings flow through
   `sin_guide/config/manager.py`. The hot-reload watch depends on it.

## Commands

Dependencies: `pip install -r sin_guide/requirements.txt` (plus the `tesseract-ocr` system package for OCR). Run the app with `python main.py`.

```bash
# Unit + functional tests (uses xvfb-run for headless Qt)
xvfb-run -a pytest tests/ -v

# Single test file / single test
xvfb-run -a pytest tests/test_guide_engine.py -v
xvfb-run -a pytest tests/test_timer.py -k test_name -v

# Visual regression tests only
xvfb-run -a pytest tests/visual/ -v

# Coverage (CI enforces an 80% line-coverage threshold)
xvfb-run -a pytest tests/ --cov=sin_guide --cov-report=term-missing

# Type check (CI runs it with --ignore-missing-imports)
mypy sin_guide/

# Lint
ruff check sin_guide/ tests/
```

Notes on the test setup:
- `tests/conftest.py` sets `QT_QPA_PLATFORM=offscreen` before any PySide6 import — don't import Qt at module scope in a way that bypasses this.
- `pytest-randomly` is installed, so tests run in random order; don't write order-dependent tests.
- Visual snapshot baselines are **not** checked in: `pytest_sessionstart` deletes `tests/visual/snapshots/*.png` before each run, the first execution of each visual test writes the baseline, and `pytest_sessionfinish` cleans up. `assert_matches_snapshot(pixmap, name)` compares with a 2% pixel-diff tolerance; `--update-snapshots` forces regeneration.
- `tests/conftest.py` also provides `make_step` (a `GuideStep` factory) and a `make_overlay` factory that builds a fully mocked `OverlayWindow`.

## Validation before opening a PR

1. Tests pass at 100%
2. mypy clean (no new errors)
3. ruff clean
4. If you changed UI rendering: regenerate visual snapshots and verify diffs are intentional
5. Commit message follows Conventional Commits

## Architecture

`main.py` is the entry point and composition root. `SinGuideApp` constructs every component and wires them with Qt signals — there is no DI container or service registry. Two background mechanisms drive everything:

- **Log watching**: `LogWatcherThread` (a `QThread` in `main.py`) tails `Client.txt` by file size, feeds lines to `core/log_parser.py` (regex → typed `LogEvent`s), and re-emits them as Qt signals (`zone_entered`, `level_up`, etc.). `SinGuideApp` routes those into the overlay, `CampaignTimer`, and `GuideEngine` — zone entry is what triggers auto-advance and timer pause/resume.
- **Focus tracking**: `overlay/window_tracker.py` finds the PoE2 window via python-xlib/xprop. `SinGuideApp` polls it on `QTimer`s (500ms focus check with a debounce counter before hiding; 50ms raise-poll to keep the overlay above the game).

Key data flows that span multiple files:

- **Guide**: `data/guides/poe2_campaign.json` (281 steps, acts 1–7) → `core/guide_engine.py` loads steps and filters by current zone + tags (league-start, optional) → `overlay/step_renderer.py` / `overlay/main_window.py` render the visible window of steps.
- **Gems**: `utils/pob_parser.py` imports a build (pobb.in URL or PoB XML) → `core/gem_ocr.py` screenshots the in-game gem panel and runs Tesseract with preprocessing + `difflib` fuzzy matching (≥80%) against `data/gems/poe2_gems.json` → `core/gem_cutter.py` intersects OCR results with the build's gems → `overlay/gem_widget.py` displays available/missing/upcoming grouped by type (skill/spirit/support).
- **Config**: `config/manager.py` reads/writes `~/.config/sin_guide/config.json`, merging over `config/defaults.py` and backing up corrupted files. Components read via dotted keys (`config.get("overlay.transparency")`). The settings dialog (`overlay/settings_panel.py`) writes through the manager and the overlay calls `reload_config()` afterward.
- **EXP**: `core/exp_calculator.py` implements the Mobalytics effective-EXP formula using `data/zones.json` zone-to-level mappings.
- **Client.txt discovery**: `utils/steam_discovery.py` parses Steam's VDF library files to locate the Proton prefix and `Client.txt`; `main.py` falls back to a manual setting if discovery fails.

The README's "Architecture" section has the full file tree and is kept accurate.

## Git workflow & CI

- Branching: `feature/<name>` off `dev` → squash-merge PR into `dev` → periodic `dev` → `main` release PRs (tagged). `main` and `dev` are protected — no direct pushes. Hotfixes branch from `main` and are merged back into `dev`. See `docs/development/branching-strategy.md`.
- CI (`.github/workflows/ci.yml`) runs on PRs/pushes to `dev` and `main`: ruff → mypy → tests with coverage → visual tests → 80% coverage threshold check.
- Additional AI-driven workflows exist (`ai-fix.yml`, `ai-review.yml`, `auto-merge.yml`, etc.); the `ai-fix` flow only triggers on the `ai-fix` label. Escape hatches are documented at the bottom of README.md.
