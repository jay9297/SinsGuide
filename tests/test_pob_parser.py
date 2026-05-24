"""Tests for PoB parser — XML extraction from encoded builds."""
from __future__ import annotations

import base64
import zlib

import pytest

from sin_guide.utils.pob_parser import Build, GemSetup, PoBParser


def encode_xml(xml: str) -> str:
    """Encode XML the same way pobb.in does: zlib compress + base64 urlsafe."""
    compressed = zlib.compress(xml.encode("utf-8"))
    return base64.urlsafe_b64encode(compressed).rstrip(b"=").decode("ascii")


@pytest.fixture()
def parser():
    return PoBParser()


@pytest.fixture()
def character_level_xml():
    """PoB XML with character level 42."""
    xml = """<PathOfBuilding version="3.0">Test Build</PathOfBuilding>
<ClassName>Witch</ClassName>
<Level>42</Level>
<Gem name="Fireball" level="20" enabled="true"/>
"""
    return encode_xml(xml)


@pytest.fixture()
def gem_level_xml():
    """PoB XML with multiple gems at different levels."""
    xml = """<PathOfBuilding version="3.0">Spark Build</PathOfBuilding>
<ClassName>Sorceress</ClassName>
<Level>85</Level>
<Gem name="Spark" level="20" enabled="true"/>
<Gem name="Herald of Thunder" level="15" enabled="true"/>
<Gem name="Lightning Bolt" level="10" enabled="true"/>
"""
    return encode_xml(xml)


@pytest.fixture()
def no_gems_xml():
    """PoB XML with no gems."""
    xml = """<PathOfBuilding version="3.0">Empty Build</PathOfBuilding>
<ClassName>Mercenary</ClassName>
<Level>30</Level>
"""
    return encode_xml(xml)


class TestPoBParser:
    def test_extracts_character_level(self, parser, character_level_xml):
        build = parser._decode(character_level_xml)
        assert build is not None
        assert build.level == 42

    def test_extracts_gem_levels(self, parser, gem_level_xml):
        build = parser._decode(gem_level_xml)
        assert build is not None
        assert len(build.gems) == 3
        assert build.gems[0].name == "Spark"
        assert build.gems[0].level == 20
        assert build.gems[1].name == "Herald of Thunder"
        assert build.gems[1].level == 15
        assert build.gems[2].name == "Lightning Bolt"
        assert build.gems[2].level == 10

    def test_no_gems_returns_empty_list(self, parser, no_gems_xml):
        build = parser._decode(no_gems_xml)
        assert build is not None
        assert build.gems == []
        assert build.level == 30
        assert build.class_name == "Mercenary"

    def test_extracts_build_name_and_class(self, parser, character_level_xml):
        build = parser._decode(character_level_xml)
        assert build is not None
        assert build.name == "Test Build"
        assert build.class_name == "Witch"

    def test_invalid_code_returns_none(self, parser):
        build = parser._decode("not-valid-base64!!!")
        assert build is None

    def test_parse_url_invalid_pob_url(self, parser):
        build = parser.parse_url("https://example.com/not-a-pob")
        assert build is None

    def test_gem_setup_dataclass(self):
        gem = GemSetup(name="Fireball", level=20, links=["Support1"])
        assert gem.name == "Fireball"
        assert gem.level == 20
        assert gem.links == ["Support1"]

    def test_build_dataclass(self):
        build = Build(
            name="Test",
            class_name="Witch",
            level=42,
            gems=[GemSetup("Fireball", 20, [])],
            tree_url="https://pobb.in/tree/abc",
        )
        assert build.name == "Test"
        assert build.class_name == "Witch"
        assert build.level == 42
        assert len(build.gems) == 1
        assert build.tree_url == "https://pobb.in/tree/abc"
