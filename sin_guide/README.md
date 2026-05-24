# Sin's Guide

A Path of Exile 2 campaign tracker and overlay for Linux, inspired by Lailloken's Exile-UI Act Tracker.

## Features

- **Automated Campaign Guide**: Step-by-step PoE2 leveling guide with conditional filtering
- **Zone-Based View**: Shows only steps for your current zone + next zone preview
- **Campaign Timer**: Track act completion times with CSV export
- **Effective EXP Display**: Level vs zone comparison using the Mobalytics formula
- **PoB/pobb.in Import**: Import builds for gem tracking
- **Conditional Engine**: Toggle league-start mode and optional steps
- **Minimalist Overlay**: Clean, transparent, draggable window
- **Settings Panel**: Adjust transparency, font size, hotkeys, and toggles

## Requirements

- Python 3.12+
- Linux with X11 (XWayland supported for PoE2 Proton)
- Path of Exile 2 via Steam/Proton

## Installation

```bash
git clone <repo-url>
cd sin_guide
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
python main.py
```

The overlay will:
1. Auto-discover your Steam Proton prefix for PoE2
2. Load the campaign guide
3. Show the overlay window
4. Track your progress via Client.txt log parsing

## Default Hotkeys

- **F3**: Previous guide step
- **F4**: Next guide step

## Settings

Right-click the overlay or edit `~/.config/sin_guide/config.json`.

## Architecture

```
sin_guide/
├── main.py                 # Entry point
├── config/
│   ├── defaults.py         # Default configuration values
│   └── manager.py          # Config manager with hot-reload
├── core/
│   ├── guide_engine.py     # Conditional step filtering
│   ├── log_parser.py       # Client.txt event parser
│   ├── timer.py            # Campaign timer with CSV export
│   ├── exp_calculator.py   # Mobalytics EXP formula
│   ├── gem_cutter.py       # Gem availability & build matching
│   └── gem_ocr.py          # Tesseract OCR for gem scanning
├── data/
│   ├── gems/
│   │   └── poe2_gems.json  # Gem database (skill/spirit/support)
│   ├── guides/
│   │   ├── poe2_campaign.json  # Campaign guide
│   │   └── generate_guide.py   # Guide data generator
│   └── zones.json          # Zone-to-level mappings
├── overlay/
│   ├── main_window.py      # PySide6 overlay UI
│   ├── gem_widget.py       # Gem availability display widget
│   ├── step_renderer.py    # Guide step rendering logic
│   ├── settings_panel.py   # Settings dialog
│   └── window_tracker.py   # X11 game window tracking
└── utils/
    ├── steam_discovery.py  # Proton prefix auto-discovery
    └── pob_parser.py       # PoB/pobb.in import
```

## License

MIT
