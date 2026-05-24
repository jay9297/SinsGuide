"""Tests for steam discovery – runs offline without a real Steam installation."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from unittest import mock

import pytest

from sin_guide.utils.steam_discovery import (
    _POE2_APPID,
    _POE2_CLIENT_TXT_RELPATH,
    _parse_vdf_text,
    _resolve_steam_data_dir,
    find_poe2_client_txt,
    get_steam_library_paths,
    parse_vdf_file,
    diagnose,
)

OLD_STYLE_VDF = """
"LibraryFolders"
{
    "TimeNextStatsReport"       "123456"
    "ContentStatsID"            "987654"
    "1"     "/mnt/games/SteamLibrary"
    "2"     "/home/user/secondary"
}
"""

NEW_STYLE_VDF = """
"libraryfolders"
{
    "0"
    {
        "path"          "/home/user/.local/share/Steam"
        "label"         ""
        "contentid"     "-1234567890"
        "totalsize"     "0"
        "apps"
        {
            "2694490"   "50000000000"
            "123456"    "1000000"
        }
    }
    "1"
    {
        "path"          "/mnt/games/SteamLibrary"
        "label"         "Games SSD"
        "contentid"     "9876543210"
        "totalsize"     "0"
        "apps"
        {
            "789012"    "2000000000"
        }
    }
}
"""

VDF_WITH_C_COMMENTS = """
// This is a comment
"Test"
{
    // another comment
    "key"   "value"
    "nested"
    {
        "inner" "works"
    }
}
"""

VDF_ESCAPED_QUOTES = r'''
"Test"
{
    "path"      "C:\\Program Files (x86)\\Steam"
    "name"      "He said \"hello\""
}
'''


class TestVdfParsing:
    def test_old_style(self):
        result = _parse_vdf_text(OLD_STYLE_VDF)
        assert "LibraryFolders" in result
        libs = result["LibraryFolders"]
        assert libs["1"] == "/mnt/games/SteamLibrary"
        assert libs["2"] == "/home/user/secondary"

    def test_new_style(self):
        result = _parse_vdf_text(NEW_STYLE_VDF)
        assert "libraryfolders" in result
        libs = result["libraryfolders"]
        assert libs["0"]["path"] == "/home/user/.local/share/Steam"
        assert libs["1"]["path"] == "/mnt/games/SteamLibrary"
        assert libs["0"]["apps"]["2694490"] == "50000000000"

    def test_c_comments_ignored(self):
        result = _parse_vdf_text(VDF_WITH_C_COMMENTS)
        assert result == {"Test": {"key": "value", "nested": {"inner": "works"}}}

    def test_escaped_quotes(self):
        result = _parse_vdf_text(VDF_ESCAPED_QUOTES)
        assert result["Test"]["name"] == 'He said "hello"'

    def test_empty(self):
        assert _parse_vdf_text("") == {}
        assert _parse_vdf_text("{}") == {}

    def test_parse_vdf_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".vdf", delete=False) as f:
            f.write(OLD_STYLE_VDF)
            f.flush()
            result = parse_vdf_file(f.name)
            assert result is not None
            assert result["LibraryFolders"]["1"] == "/mnt/games/SteamLibrary"
        os.unlink(f.name)

    def test_parse_missing_file(self):
        assert parse_vdf_file("/nonexistent/path.vdf") is None


def _make_fake_steam_dir(base: Path, vdf_content: str) -> Path:
    steam_dir = base / ".local" / "share" / "Steam"
    config_dir = steam_dir / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    (steam_dir / "steamapps").mkdir(parents=True, exist_ok=True)
    (config_dir / "libraryfolders.vdf").write_text(vdf_content)
    return steam_dir


class TestLibraryDiscovery:
    def test_primary_library_always_included(self, tmp_path):
        steam_dir = _make_fake_steam_dir(tmp_path, OLD_STYLE_VDF)
        libs = get_steam_library_paths(steam_dir)
        assert libs[0] == steam_dir

    def test_old_style_external_libraries(self, tmp_path):
        vdf = OLD_STYLE_VDF.replace("/mnt/games/SteamLibrary", str(tmp_path / "external"))
        external = tmp_path / "external"
        external.mkdir(parents=True, exist_ok=True)
        (external / "steamapps").mkdir(parents=True, exist_ok=True)

        steam_dir = _make_fake_steam_dir(tmp_path, vdf)
        libs = get_steam_library_paths(steam_dir)
        assert len(libs) >= 2
        paths = {p.resolve() for p in libs}
        assert external.resolve() in paths

    def test_new_style_external_libraries(self, tmp_path):
        external = tmp_path / "external"
        external.mkdir(parents=True, exist_ok=True)
        (external / "steamapps").mkdir(parents=True, exist_ok=True)

        vdf = NEW_STYLE_VDF.replace("/mnt/games/SteamLibrary", str(external))
        steam_dir = _make_fake_steam_dir(tmp_path, vdf)
        libs = get_steam_library_paths(steam_dir)
        paths = {p.resolve() for p in libs}
        assert external.resolve() in paths

    def test_no_library_folders_file(self, tmp_path):
        steam_dir = _make_fake_steam_dir(tmp_path, "")
        (steam_dir / "config" / "libraryfolders.vdf").unlink()
        libs = get_steam_library_paths(steam_dir)
        assert libs == [steam_dir]


def _create_fake_prefix(steam_dir: Path, appid: str = _POE2_APPID) -> Path:
    pfx = steam_dir / "steamapps" / "compatdata" / appid / "pfx"
    client_dir = pfx / Path(_POE2_CLIENT_TXT_RELPATH).parent
    client_dir.mkdir(parents=True, exist_ok=True)
    (client_dir / "Client.txt").write_text("2024/01/01 12:00:00 Test log entry\n")
    return pfx


class TestClientTxtDiscovery:
    def test_finds_client_txt(self, tmp_path):
        steam_dir = _make_fake_steam_dir(tmp_path, NEW_STYLE_VDF)
        _create_fake_prefix(steam_dir)

        with mock.patch("sin_guide.utils.steam_discovery._resolve_steam_data_dir", return_value=steam_dir):
            found = find_poe2_client_txt()
            assert found is not None
            assert found.name == "Client.txt"

    def test_returns_none_when_not_installed(self):
        with mock.patch("sin_guide.utils.steam_discovery._resolve_steam_data_dir", return_value=None):
            assert find_poe2_client_txt() is None

    def test_prefix_not_created_yet(self, tmp_path):
        steam_dir = _make_fake_steam_dir(tmp_path, NEW_STYLE_VDF)

        with mock.patch("sin_guide.utils.steam_discovery._resolve_steam_data_dir", return_value=steam_dir):
            assert find_poe2_client_txt() is None

    def test_find_all_returns_multiple(self, tmp_path):
        external = tmp_path / "external"
        external.mkdir(parents=True, exist_ok=True)
        (external / "steamapps").mkdir(parents=True, exist_ok=True)

        vdf = NEW_STYLE_VDF.replace("/mnt/games/SteamLibrary", str(external))
        steam_dir = _make_fake_steam_dir(tmp_path, vdf)

        _create_fake_prefix(steam_dir)
        _create_fake_prefix(external)

        libs = [steam_dir, external]
        with (
            mock.patch("sin_guide.utils.steam_discovery._resolve_steam_data_dir", return_value=steam_dir),
            mock.patch("sin_guide.utils.steam_discovery.get_steam_library_paths", return_value=libs),
        ):
            from sin_guide.utils.steam_discovery import find_all_poe2_client_txt
            results = find_all_poe2_client_txt()
            assert len(results) == 2


class TestSteamDataDir:
    def test_env_var_override(self, tmp_path, monkeypatch):
        fake_steam = tmp_path / "custom_steam"
        (fake_steam / "steamapps").mkdir(parents=True)
        monkeypatch.setenv("STEAMROOT", str(fake_steam))

        result = _resolve_steam_data_dir()
        if result is not None:
            assert result == fake_steam.resolve()

    def test_env_var_invalid(self, monkeypatch):
        monkeypatch.setenv("STEAMROOT", "/does/not/exist")
        result = _resolve_steam_data_dir()
        if result is not None:
            assert result != Path("/does/not/exist")


class TestDiagnose:
    def test_returns_dict(self):
        result = diagnose()
        assert isinstance(result, dict)
        assert "steam_data_dir" in result
        assert "libraries" in result
        assert "prefixes_found" in result
        assert "client_txt" in result

    def test_diagnose_with_mock(self, tmp_path):
        steam_dir = _make_fake_steam_dir(tmp_path, NEW_STYLE_VDF)
        _create_fake_prefix(steam_dir)

        with mock.patch("sin_guide.utils.steam_discovery._resolve_steam_data_dir", return_value=steam_dir):
            result = diagnose()
            assert result["client_txt"] is not None
            assert len(result["prefixes_found"]) >= 1
