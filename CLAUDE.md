# Sin's Guide — Agent Instructions

You are working on Sin's Guide, a Path of Exile 2 campaign tracker overlay
written in Python 3.12 with PySide6. It runs on Linux/X11 (XWayland supported).

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

## How to test changes

```bash
# Unit + functional tests (uses xvfb-run for headless Qt)
xvfb-run -a pytest tests/ -v

# Visual regression tests only
xvfb-run -a pytest tests/visual/ -v

# Coverage
xvfb-run -a pytest tests/ --cov=sin_guide --cov-report=term-missing

# Type check
mypy sin_guide/

# Lint
ruff check sin_guide/ tests/
```

## How to validate before opening a PR

1. Tests pass at 100%
2. mypy clean (no new errors)
3. ruff clean
4. If you changed UI rendering: regenerate visual snapshots and verify diffs are intentional
5. Commit message follows Conventional Commits

## Project structure

See README.md "Architecture" section — it's accurate and current.
