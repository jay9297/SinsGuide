"""Guaranteed league mechanic rewards per campaign zone.

Source: https://mobalytics.gg/poe-2/guides/league-mechanic-campaign-reward-cheat-sheet

Each value is the guaranteed reward from completing the league mechanic in that zone.
Format rule: values must be <= 22 chars to fit "League: $reward" within 30 chars.
"""

ZONE_LEAGUE_REWARDS: dict[str, str] = {
    # ── Act 1 ──────────────────────────────────────────────
    "Clearfell": "Orb of Transmutation",
    "The Mud Burrow": "Orb of Augmentation",
    "The Grelwood": "Orb of Transmutation",
    "The Red Vale": "Uncut Skill Gem (2)",
    "The Grim Tangle": "Uncut Skill Gem (3)",
    "The Cemetery of the Eternals": "Regal Orb",
    "The Tomb of the Consort": "Amulet",
    "The Mausoleum of the Praetor": "Lesser Rune",
    "The Hunting Grounds": "Exalted Orb",
    "Ogham Farmlands": "Uncut Skill Gem (4)",
    "Freythorn": "Uncut Support Gem",
    "Ogham Village": "Artificer's Orb",
    "The Manor Ramparts": "Uncut Skill Gem (5)",
    "Ogham Manor": "Orb of Alchemy",
    # ── Act 2 ──────────────────────────────────────────────
    "Vastiri Outskirts": "Exalted Orb",
    "Mawdun Quarry": "Uncut Spirit Gem (5)",
    "Mawdun Mine": "Uncut Support Gem (2)",
    "Traitor's Passage": "Artificer's Orb",
    "The Halani Gates": "Exalted Orb",
    "Keth": "Gemcutter's Prism",
    "The Lost City": "Orb of Alchemy",
    "Buried Shrines": "Lesser Jeweller's Orb",
    "Mastodon Badlands": "Regal Orb",
    "The Bone Pits": "Exalted Orb",
    "The Valley of the Titans": "Unique",
    "The Titan Grotto": "Chance Shard",
    "Deshar": "Lesser Rune",
    "The Spires of Deshar": "Gemcutter's Prism",
    # ── Act 3 ──────────────────────────────────────────────
    "Sandswept Marsh": "Uncut Support Gem (3)",
    "Jungle Ruins": "Orb of Alchemy",
    "The Venom Crypts": "Magic Ring",
    "Infested Barrens": "Exalted Orb",
    "The Azak Bog": "Rune",
    "Chimeral Wetlands": "Uncut Skill Gem (9)",
    "Jiquani's Machinarium": "Artificer's Orb",
    "Jiquani's Sanctum": "Exalted Orb",
    "The Drowned City": "Uncut Support Gem (3)",
    "The Molten Vault": "Unique",
    "The Apex of Filth": "Vaal Orb",
    # ── Act 4 ──────────────────────────────────────────────
    "Kedge Bay": "Exalted Orb",
    "Isle of Kin": "Gemcutter's Prism",
    "Volcanic Warrens": "Uncut Support Gem (4)",
    "Whakapanu Island": "Artificer's Orb",
    "Singing Caverns": "Magic Charm",
    "Abandoned Prison": "Exalted Orb",
    "Solitary Confinement": "Rune",
    "Shrike Island": "Uncut Support Gem (4)",
    "Eye of Hinekora": "Chaos Orb",
    "Arastas": "Uncut Skill Gem (12)",
    "The Excavation": "Rare Amulet",
    "Ngakanu": "Greater Jeweller's Orb",
    "Heart of the Tribe": "Uncut Spirit Gem (12)",
    # ── Interlude 1 ────────────────────────────────────────
    "Holten": "Greater Rune",
    "Wolvenhold": "Greater Orb of Augment",
    # ── Interlude 2 ────────────────────────────────────────
    "The Khari Crossing": "Gemcutter's Prism",
    "Sel Khari Sanctuary": "Orb of Chance",
    "Qimah": "Exalted Orb",
    # ── Interlude 3 ────────────────────────────────────────
    "Kriar Village": "Greater Rune",
    "Howling Caves": "Chaos Orb",
    "Kriar Peaks": "Greater Orb of Transm.",
}

ZONES_WITHOUT_REWARDS = {
    "The Riverbank",
    "The Clearfell Encampment",
    "Ardura Caravan",
    "Ziggurat Encampment",
    "Trial of the Sekhemas",
    "The Dreadnought",
    "The Dreadnought Vanguard",
    "The Path of Mourning",
}
