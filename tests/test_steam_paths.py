"""Tests for steam discovery – runs offline without a real Steam installation."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from unittest import mock


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


def _create_fake_common_layout(steam_dir: Path) -> Path:
    """Drop a Client.txt into ``steamapps/common/Path of Exile 2/logs/``.

    Mirrors the layout observed on Bazzite / modern PoE2 installs where
    the game writes its log next to the binary rather than inside the
    Proton prefix's Documents folder.
    """
    from sin_guide.utils.steam_discovery import _POE2_CLIENT_TXT_COMMON_RELPATH
    log_path = steam_dir / _POE2_CLIENT_TXT_COMMON_RELPATH
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text("2024/01/01 12:00:00 Test log entry\n")
    return log_path


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


class TestClientTxtCommonLayoutDiscovery:
    """Cover the modern PoE2 layout where ``Client.txt`` lives next to the
    game binary under ``steamapps/common/<Game>/logs/`` rather than inside
    the Proton prefix.  Reproduces the Bazzite install observed in
    https://github.com/jay9297/SinsGuide (regression test for the
    "Client.txt not detected" bug)."""

    def test_finds_client_txt_in_common_logs(self, tmp_path):
        steam_dir = _make_fake_steam_dir(tmp_path, NEW_STYLE_VDF)
        _create_fake_common_layout(steam_dir)

        with mock.patch("sin_guide.utils.steam_discovery._resolve_steam_data_dir", return_value=steam_dir):
            found = find_poe2_client_txt()
            assert found is not None
            assert found.name == "Client.txt"
            assert "common" in found.parts

    def test_finds_client_txt_on_external_library(self, tmp_path):
        external = tmp_path / "external"
        external.mkdir(parents=True, exist_ok=True)
        (external / "steamapps").mkdir(parents=True, exist_ok=True)

        vdf = NEW_STYLE_VDF.replace("/mnt/games/SteamLibrary", str(external))
        steam_dir = _make_fake_steam_dir(tmp_path, vdf)
        _create_fake_common_layout(external)

        libs = [steam_dir, external]
        with (
            mock.patch("sin_guide.utils.steam_discovery._resolve_steam_data_dir", return_value=steam_dir),
            mock.patch("sin_guide.utils.steam_discovery.get_steam_library_paths", return_value=libs),
        ):
            found = find_poe2_client_txt()
            assert found is not None
            assert str(found).startswith(str(external))

    def test_prefix_path_wins_when_both_layouts_present(self, tmp_path):
        """If the prefix path also exists (older install), keep preferring
        it so the documented behaviour is preserved."""
        from sin_guide.utils.steam_discovery import _POE2_CLIENT_TXT_RELPATH
        steam_dir = _make_fake_steam_dir(tmp_path, NEW_STYLE_VDF)
        _create_fake_prefix(steam_dir)
        _create_fake_common_layout(steam_dir)

        with mock.patch("sin_guide.utils.steam_discovery._resolve_steam_data_dir", return_value=steam_dir):
            found = find_poe2_client_txt()
            assert found is not None
            assert _POE2_CLIENT_TXT_RELPATH in str(found)

    def test_find_all_returns_both_layouts(self, tmp_path):
        """A prefix-layout and a common-layout Client.txt in the same
        library are distinct candidates — find_all must return both,
        prefix first (matching find_poe2_client_txt's preference)."""
        from sin_guide.utils.steam_discovery import (
            _POE2_CLIENT_TXT_RELPATH,
            find_all_poe2_client_txt,
        )
        steam_dir = _make_fake_steam_dir(tmp_path, NEW_STYLE_VDF)
        _create_fake_prefix(steam_dir)
        common = _create_fake_common_layout(steam_dir)

        with mock.patch("sin_guide.utils.steam_discovery._resolve_steam_data_dir", return_value=steam_dir):
            results = find_all_poe2_client_txt()

        assert len(results) == 2
        assert _POE2_CLIENT_TXT_RELPATH in str(results[0])
        assert results[1] == common

    def test_returns_none_when_no_layout_has_client_txt(self, tmp_path):
        steam_dir = _make_fake_steam_dir(tmp_path, NEW_STYLE_VDF)

        with mock.patch("sin_guide.utils.steam_discovery._resolve_steam_data_dir", return_value=steam_dir):
            assert find_poe2_client_txt() is None


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
