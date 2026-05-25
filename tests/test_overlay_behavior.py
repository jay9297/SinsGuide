"""Behavioral tests for OverlayWindow — player level, zone levels, EXP display."""
from __future__ import annotations




class TestPlayerLevelTracking:
    def test_initial_player_level_is_none(self, make_overlay):
        overlay = make_overlay(steps=[])
        assert overlay._get_player_level() is None

    def test_handle_level_up_stores_player_level(self, make_overlay):
        overlay = make_overlay(steps=[])
        overlay.handle_level_up(7)
        assert overlay._get_player_level() == 7

    def test_multiple_level_ups_track_highest(self, make_overlay):
        overlay = make_overlay(steps=[])
        overlay.handle_level_up(3)
        overlay.handle_level_up(7)
        overlay.handle_level_up(5)
        assert overlay._get_player_level() == 7


class TestZoneLevelMapping:
    ZONE_LEVELS = {
        "The Riverbank": 1,
        "The Clearfell Encampment": 2,
        "Clearfell": 2,
        "The Mud Burrow": 3,
        "The Grelwood": 4,
        "The Red Vale": 5,
        "The Grim Tangle": 6,
        "The Cemetery of the Eternals": 7,
        "The Mausoleum of the Praetor": 8,
        "The Tomb of the Consort": 8,
        "The Hunting Grounds": 9,
        "Freythorn": 10,
        "Ogham Farmlands": 11,
        "Ogham Village": 12,
        "The Manor Ramparts": 13,
        "Ogham Manor": 14,
        "Vastiri Outskirts": 13,
        "Ardura Caravan": 13,
        "Mawdun Quarry": 14,
        "Mawdun Mine": 15,
        "Traitor's Passage": 16,
        "The Halani Gates": 17,
        "Trial of the Sekhemas": 18,
        "Keth": 19,
        "The Lost City": 20,
        "Buried Shrines": 21,
        "Mastodon Badlands": 22,
        "The Bone Pits": 22,
        "The Valley of the Titans": 23,
        "The Titan Grotto": 23,
        "Deshar": 24,
        "The Path of Mourning": 25,
        "The Spires of Deshar": 25,
        "The Dreadnought": 26,
        "The Dreadnought Vanguard": 27,
        "Sandswept Marsh": 28,
        "Ziggurat Encampment": 28,
        "Jungle Ruins": 29,
        "The Venom Crypts": 30,
        "Infested Barrens": 31,
        "The Azak Bog": 32,
        "Chimeral Wetlands": 33,
        "Jiquani's Machinarium": 34,
        "Jiquani's Sanctum": 35,
        "The Drowned City": 36,
        "The Molten Vault": 37,
        "The Apex of Filth": 38,
        "Kedge Bay": 40,
        "Isle of Kin": 41,
        "Volcanic Warrens": 40,
        "Whakapanu Island": 42,
        "Singing Caverns": 42,
        "Abandoned Prison": 43,
        "Solitary Confinement": 43,
        "Shrike Island": 44,
        "Eye of Hinekora": 45,
        "The Excavation": 46,
        "Arastas": 46,
        "Ngakanu": 47,
        "Heart of the Tribe": 48,
        "Holten": 49,
        "Wolvenhold": 50,
        "The Khari Crossing": 52,
        "Qimah": 54,
        "Sel Khari Sanctuary": 55,
        "Kriar Village": 57,
        "Howling Caves": 58,
        "Kriar Peaks": 60,
    }

    def test_all_zones_have_level(self, make_overlay):
        overlay = make_overlay(steps=[])
        missing = []
        for zone in self.ZONE_LEVELS:
            level = overlay._estimate_zone_level(zone)
            if level is None:
                missing.append(zone)
        assert not missing, f"Zones missing level mapping: {missing}"

    def test_zone_level_values_correct(self, make_overlay):
        overlay = make_overlay(steps=[])
        for zone, expected in self.ZONE_LEVELS.items():
            actual = overlay._estimate_zone_level(zone)
            assert actual == expected, f"{zone}: expected {expected}, got {actual}"
