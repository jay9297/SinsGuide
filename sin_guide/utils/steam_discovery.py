"""
Steam Path Discovery for Path of Exile 2 (AppID: 2694490) on Linux.

Finds the Client.txt log file inside Proton compatdata without external
dependencies.  Handles native Steam, Flatpak, Snap, and custom installations.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Iterator

_POE2_APPID = "2694490"

_POE2_CLIENT_TXT_RELPATH = (
    "drive_c/users/steamuser/Documents/My Games/Path of Exile 2/Client.txt"
)

# `~/.steam/steam` is a symlink shim Valve ships; it almost always resolves to the real data dir.
_CANDIDATE_STEAM_DIRS = [
    "~/.steam/steam",
    "~/.local/share/Steam",
    "~/.var/app/com.valvesoftware.Steam/.local/share/Steam",   # Flatpak
    "~/.var/app/com.valvesoftware.Steam/data/steam",           # Flatpak (alt)
    "~/snap/steam/common/.local/share/Steam",                  # Snap
    "~/.steam/debian-installation",                            # older Debian
]

_STEAM_ENV_VARS = ("STEAMROOT", "STEAM_DIR")


def _parse_vdf_text(text: str) -> dict:
    """Parse Valve KeyValues (VDF) text into a nested dict.

    Handles both old-style ``"LibraryFolders" { "1" "/path" }`` and
    new-style ``"libraryfolders" { "0" { "path" "..." "apps" {...} } }``.
    """
    lines = _tokenize_vdf(text)
    if not lines:
        return {}
    it = iter(lines)
    try:
        root_key = next(it)
    except StopIteration:
        return {}
    if root_key == "{":
        try:
            root_key = next(it)
            if root_key == "}":
                return {}
        except StopIteration:
            return {}
    return {root_key: _parse_block(it)}


def _tokenize_vdf(text: str) -> list[str]:
    """Split VDF text into tokens: keys, values, and structural markers."""
    text = re.sub(r"//[^\n]*", "", text)
    tokens: list[str] = []
    for match in re.finditer(r'"(?:[^"\\]|\\.)*"|[{}]', text):
        token = match.group(0)
        if token.startswith('"'):
            token = token[1:-1].replace("\\n", "\n").replace("\\t", "\t").replace('\\"', '"').replace("\\\\", "\\")
        tokens.append(token)
    return tokens


def _parse_block(it: Iterator[str]) -> dict:
    """Parse a ``{ key value ... }`` block."""
    result: dict = {}
    while True:
        try:
            token = next(it)
        except StopIteration:
            return result
        if token == "}":
            return result
        if token == "{":
            continue
        key = token
        try:
            next_token = next(it)
        except StopIteration:
            result[key] = ""
            return result
        result[key] = _parse_block(it) if next_token == "{" else next_token
    return result


def parse_vdf_file(path: str | Path) -> dict | None:
    """Parse a VDF file on disk, returning the root dict or ``None``."""
    try:
        with open(path, "r", encoding="utf-8", errors="surrogateescape") as fh:
            return _parse_vdf_text(fh.read())
    except (OSError, UnicodeDecodeError):
        return None


def _resolve_steam_data_dir() -> Path | None:
    """Find the Steam data directory that contains ``steamapps/``."""
    for var in _STEAM_ENV_VARS:
        val = os.environ.get(var)
        if val:
            p = Path(val).expanduser().resolve()
            if _is_steam_data_dir(p):
                return p

    for candidate in _CANDIDATE_STEAM_DIRS:
        p = Path(candidate).expanduser().resolve()
        if _is_steam_data_dir(p):
            return p

    p = Path("~/.steam/steam").expanduser()
    if p.is_symlink():
        resolved = p.resolve()
        if _is_steam_data_dir(resolved):
            return resolved

    return None


def _is_steam_data_dir(path: Path) -> bool:
    """Does *path* look like a Steam data directory?"""
    return (path / "steamapps").is_dir()


def _read_library_folders(steam_data_dir: Path) -> dict:
    """Parse ``libraryfolders.vdf`` and return the library-folders sub-dict.

    Tries the newer ``config/libraryfolders.vdf`` first, then falls back
    to ``steamapps/libraryfolders.vdf``.
    """
    for relpath in ("config/libraryfolders.vdf", "steamapps/libraryfolders.vdf"):
        vdf = parse_vdf_file(steam_data_dir / relpath)
        if vdf is None:
            continue

        for container_key in ("libraryfolders", "LibraryFolders", "libraryfolder", "LibraryFolder"):
            if container_key in vdf:
                raw = vdf[container_key]
                if isinstance(raw, dict):
                    for noise in ("contentstatsid", "ContentStatsID", "TimeNextStatsReport"):
                        raw.pop(noise, None)
                    return raw

        vdf.pop("contentstatsid", None)
        vdf.pop("ContentStatsID", None)
        vdf.pop("TimeNextStatsReport", None)

        has_path_subkeys = any(isinstance(v, dict) and "path" in v for v in vdf.values())
        return vdf if has_path_subkeys else {}

    return {}


def get_steam_library_paths(steam_data_dir: Path) -> list[Path]:
    """Return all Steam library root paths (the folders containing ``steamapps/``)."""
    lib_folders = _read_library_folders(steam_data_dir)

    libraries: list[Path] = [steam_data_dir]

    for key, value in lib_folders.items():
        if not key.isdigit():
            continue

        if isinstance(value, dict):
            path_str = str(value.get("path", ""))
        else:
            path_str = str(value)

        if path_str:
            lib_path = Path(path_str).expanduser()
            if lib_path.is_dir() and lib_path not in libraries:
                libraries.append(lib_path)

    return libraries


def get_proton_prefix_dirs(appid: str = _POE2_APPID) -> list[Path]:
    """Return all ``compatdata/<appid>/pfx`` Proton prefix directories.

    Compatdata lives in ``<library>/steamapps/compatdata/<appid>``.
    Symlinks are not resolved here since that could break Proton's
    internal path expectations.
    """
    steam_dir = _resolve_steam_data_dir()
    if steam_dir is None:
        return []

    libraries = get_steam_library_paths(steam_dir)
    prefixes: list[Path] = []

    for lib in libraries:
        pfx = lib / "steamapps" / "compatdata" / appid / "pfx"
        if pfx.is_dir():
            prefixes.append(pfx)

    return prefixes


def find_poe2_client_txt() -> Path | None:
    """Find the Path of Exile 2 ``Client.txt`` log file.

    Returns the first valid path found, or ``None`` if PoE2 is not
    installed or has never been launched on this machine.
    """
    rel = _POE2_CLIENT_TXT_RELPATH
    for pfx in get_proton_prefix_dirs():
        candidate = pfx / rel
        if candidate.resolve().is_file():
            return candidate
    return None


def find_all_poe2_client_txt() -> list[Path]:
    """Return **all** PoE2 ``Client.txt`` files found across all prefixes."""
    rel = _POE2_CLIENT_TXT_RELPATH
    results: list[Path] = []
    for pfx in get_proton_prefix_dirs():
        candidate = pfx / rel
        if candidate.resolve().is_file():
            results.append(candidate)
    return results


def diagnose() -> dict:
    """Return diagnostic info about the current Steam environment."""
    steam_dir = _resolve_steam_data_dir()
    libraries = get_steam_library_paths(steam_dir) if steam_dir else []
    prefixes = get_proton_prefix_dirs() if steam_dir else []
    client_txt = find_poe2_client_txt()

    return {
        "steam_data_dir": str(steam_dir) if steam_dir else None,
        "libraries": [str(lib) for lib in libraries],
        "prefixes_found": [str(p) for p in prefixes],
        "client_txt": str(client_txt) if client_txt else None,
    }


# ---------------------------------------------------------------------------
# Compatibility alias — main.py imports this name.
# ---------------------------------------------------------------------------

def get_client_txt_path() -> str | None:
    """Find the PoE2 Client.txt log file. Returns path string or None."""
    result = find_poe2_client_txt()
    return str(result) if result else None
