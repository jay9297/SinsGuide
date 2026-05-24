import json

POE2_GUIDE = {
    "version": "0.1.0",
    "game": "poe2",
    "acts": [1, 2, 3, 4, 5, 6, 7],
    "steps": []
}

step_counter = 0

def add_step(act, zone, description, step_type, target="", hint="", tags=None, next_steps=None, auto_advance=None):
    global step_counter
    step_counter += 1
    step = {
        "id": f"a{act}_{zone.lower().replace(' ', '_').replace('.', '')}_{step_counter:03d}",
        "act": act,
        "zone": zone,
        "step_number": step_counter,
        "description": description,
        "type": step_type,
        "target": target,
        "hint": hint,
        "tags": tags or ["mandatory"],
        "next_steps": next_steps or [],
        "auto_advance_trigger": auto_advance
    }
    POE2_GUIDE["steps"].append(step)
    return step["id"]

a1_ids = {}
a1_ids["riverbank_01"] = add_step(1, "The Riverbank", "Follow the Tutorial and kill the Bloated Miller", "kill", "Bloated Miller", "", ["mandatory"], [], {"type": "enter_area", "target_area": "The Clearfell Encampment"})
a1_ids["clearfell_encampment_01"] = add_step(1, "The Clearfell Encampment", "Claim your Quest Reward Skill Gem from Renly", "quest_reward", "Renly", "Check Renly's Shop for any items you can afford", ["mandatory"], [])
a1_ids["clearfell_01"] = add_step(1, "Clearfell", "(Optional) Loot the Abandoned Stash in the Mysterious Campsite", "loot", "Abandoned Stash", "Contains an Uncut Skill Gem. Checkpoint nearby to make it easier to spot.", ["optional", "recommended"], [])
a1_ids["clearfell_02"] = add_step(1, "Clearfell", "(Permanent Buff) Defeat Beira of the Rotten Pack in the Middle North of the zone", "kill", "Beira of the Rotten Pack", "+10% to Cold Resistance permanent buff", ["permanent_buff"], [])
a1_ids["clearfell_03"] = add_step(1, "Clearfell", "Activate the Waypoint and enter the Mud Burrow", "travel", "Mud Burrow", "", ["mandatory"], [], {"type": "enter_area", "target_area": "The Mud Burrow"})
a1_ids["mud_burrow_01"] = add_step(1, "The Mud Burrow", "(Optional) Kill The Devourer", "kill", "The Devourer", "Level 2 Uncut Skill Gem Drop", ["optional", "recommended"], [])
a1_ids["mud_burrow_02"] = add_step(1, "The Mud Burrow", "Portal to Town and Speak to Renly for Uncut Support Gem Quest Reward", "quest_reward", "Renly", "", ["mandatory"], [])
a1_ids["grelwood_01"] = add_step(1, "The Grelwood", "Return to Clearfell via Waypoint and head North East to enter The Grelwood", "travel", "The Grelwood", "", ["mandatory"], [], {"type": "enter_area", "target_area": "The Grelwood"})
a1_ids["grelwood_02"] = add_step(1, "The Grelwood", "(Optional) Areagne's Hut: Flask Upgrades from Cauldron + Kill Areagne for Uncut Support Gem", "kill", "Areagne", "", ["optional"], [])
a1_ids["grelwood_03"] = add_step(1, "The Grelwood", "(Optional) Kill Brambleghast: Level 1 Uncut Skill Gem drop", "kill", "Brambleghast", "", ["optional"], [])
a1_ids["grelwood_04"] = add_step(1, "The Grelwood", "Activate Tree of Souls Waypoint, enter Grim Tangle and activate Waypoint, return to Grelwood", "travel", "The Grim Tangle", "", ["mandatory"], [])
a1_ids["grelwood_05"] = add_step(1, "The Grelwood", "Enter the Red Vale and activate three Rust Altars", "travel", "The Red Vale", "Entrance is usually near Brambleghast", ["mandatory"], [], {"type": "enter_area", "target_area": "The Red Vale"})
a1_ids["red_vale_01"] = add_step(1, "The Red Vale", "Kill The Rust King", "kill", "The Rust King", "Each Altar is located in a broad loop around the zone", ["mandatory"], [])
a1_ids["clearfell_encampment_02"] = add_step(1, "The Clearfell Encampment", "Portal to Town. Return all three Runed Quest Items to Renly", "quest_reward", "Renly", "", ["mandatory"], [])
a1_ids["grelwood_06"] = add_step(1, "The Grelwood", "Go to Grelwood via Waypoint. Summon Una and Runed Spike the Tree of Souls", "quest_reward", "Una", "", ["mandatory"], [])
a1_ids["clearfell_encampment_03"] = add_step(1, "The Clearfell Encampment", "Waypoint to Town and speak to Una again", "quest_reward", "Una", "", ["mandatory"], [])
a1_ids["grim_tangle_01"] = add_step(1, "The Grim Tangle", "Return to Grelwood and enter the Grim Tangle", "travel", "The Grim Tangle", "", ["mandatory"], [], {"type": "enter_area", "target_area": "The Grim Tangle"})
a1_ids["grim_tangle_02"] = add_step(1, "The Grim Tangle", "(Optional) Kill The Rotten Druid: Uncut Support Gem", "kill", "The Rotten Druid", "", ["optional"], [])
a1_ids["grim_tangle_03"] = add_step(1, "The Grim Tangle", "Enter The Cemetery of the Eternals", "travel", "The Cemetery of the Eternals", "", ["mandatory"], [], {"type": "enter_area", "target_area": "The Cemetery of the Eternals"})
a1_ids["cemetery_01"] = add_step(1, "The Cemetery of the Eternals", "(Optional) Loot the Ancient Ruins Grave Site: Random Ring", "loot", "Ancient Ruins", "", ["optional"], [])
a1_ids["cemetery_02"] = add_step(1, "The Cemetery of the Eternals", "Locate and complete Mausoleum of the Praetor and Tomb of the Consort (in any order)", "travel", "", "", ["mandatory"], [])
a1_ids["mausoleum_01"] = add_step(1, "The Mausoleum of the Praetor", "(Optional) Loot the Forgotten Riches: Gold and Random Loot", "loot", "Forgotten Riches", "", ["optional"], [])
a1_ids["mausoleum_02"] = add_step(1, "The Mausoleum of the Praetor", "Defeat Draven, Eternal Praetor", "kill", "Draven, Eternal Praetor", "", ["mandatory"], [])
a1_ids["tomb_01"] = add_step(1, "The Tomb of the Consort", "(Optional) Activate the Embattled Trove ambush and defeat Rare Eternal Knight: Uncut Support Gem", "kill", "Eternal Knight", "", ["optional"], [])
a1_ids["tomb_02"] = add_step(1, "The Tomb of the Consort", "Kill Asinia, Praetor Consort", "kill", "Asinia, Praetor Consort", "", ["mandatory"], [])
a1_ids["cemetery_03"] = add_step(1, "The Cemetery of the Eternals", "Return to Cemetery. Once both bosses killed, speak to Lachlann and open Memorial Gate", "quest_reward", "Lachlann", "", ["mandatory"], [])
a1_ids["cemetery_04"] = add_step(1, "The Cemetery of the Eternals", "Defeat Lachlann of Endless Lament", "kill", "Lachlann of Endless Lament", "", ["mandatory"], [])
a1_ids["hunting_grounds_01"] = add_step(1, "The Hunting Grounds", "Enter Hunting Grounds, Waypoint to Town and speak to Una", "quest_reward", "Una", "", ["mandatory"], [], {"type": "enter_area", "target_area": "The Hunting Grounds"})
a1_ids["hunting_grounds_02"] = add_step(1, "The Hunting Grounds", "(Permanent Buff) Kill The Crowbell: +2 Passive Skill Points", "kill", "The Crowbell", "Look for a wooden swing door with obvious arena nearby", ["permanent_buff"], [])
a1_ids["hunting_grounds_03"] = add_step(1, "The Hunting Grounds", "(Optional) Kill the Dryads at the Dryadic Ritual: Uncut Support Gem", "kill", "Dryads", "", ["optional"], [])
a1_ids["hunting_grounds_04"] = add_step(1, "The Hunting Grounds", "(Optional) Complete the Ritual Site: Level 4 Uncut Skill Gem", "loot", "Ritual Site", "", ["optional"], [])
a1_ids["hunting_grounds_05"] = add_step(1, "The Hunting Grounds", "Enter Freythorn, and activate the Waypoint", "travel", "Freythorn", "", ["mandatory"], [], {"type": "enter_area", "target_area": "Freythorn"})
a1_ids["hunting_grounds_06"] = add_step(1, "The Hunting Grounds", "Enter Ogham Village, and activate the Waypoint", "travel", "Ogham Village", "", ["mandatory"], [], {"type": "enter_area", "target_area": "Ogham Village"})
a1_ids["freythorn_01"] = add_step(1, "Freythorn", "Return to Town via Waypoint and check Una for Greater Life Flask and Greater Mana Flask if needed", "quest_reward", "Una", "", ["optional"], [])
a1_ids["freythorn_02"] = add_step(1, "Freythorn", "Locate and complete three Rituals", "travel", "", "", ["mandatory"], [])
a1_ids["freythorn_03"] = add_step(1, "Freythorn", "Activate the final Ritual and kill The King in the Mists", "kill", "The King in the Mists", "You can purchase Items from the Ritual Altar afterwards", ["mandatory"], [])
a1_ids["freythorn_04"] = add_step(1, "Freythorn", "Activate Gembloom Skull: +30 Spirit and Uncut Spirit Gem", "quest_reward", "Gembloom Skull", "", ["permanent_buff"], [])
a1_ids["clearfell_encampment_04"] = add_step(1, "The Clearfell Encampment", "Portal to Town and speak to Finn for a Quest Reward choice of Ruby/Sapphire/Topaz Charms", "quest_reward", "Finn", "A Sapphire Charm is recommended for the upcoming final Act 1 boss", ["mandatory"], [])
a1_ids["ogham_farmlands_01"] = add_step(1, "Ogham Farmlands", "Take the Waypoint to Ogham Farmlands", "travel", "Ogham Farmlands", "", ["mandatory"], [], {"type": "enter_area", "target_area": "Ogham Farmlands"})
a1_ids["ogham_farmlands_02"] = add_step(1, "Ogham Farmlands", "(Permanent Buff) Find Una's Lute in a ruined hut (behind broken carts)", "loot", "Una's Lute", "Return Lute to Una in town for +2 Passive Skill Points", ["permanent_buff"], [])
a1_ids["ogham_farmlands_03"] = add_step(1, "Ogham Farmlands", "(Optional) Kill the Rare Feral Mutt in the Crop Circle: Level 4 Uncut Skill Gem", "kill", "Feral Mutt", "", ["optional"], [])
a1_ids["ogham_farmlands_04"] = add_step(1, "Ogham Farmlands", "Enter Ogham Village", "travel", "Ogham Village", "", ["mandatory"], [], {"type": "enter_area", "target_area": "Ogham Village"})
a1_ids["ogham_village_01"] = add_step(1, "Ogham Village", "Locate Renley's Workshop Smithing Tools (Anvil Sign, Large Building)", "loot", "Smithing Tools", "Only needed on first character per league", ["league_start_only"], [])
a1_ids["ogham_village_02"] = add_step(1, "Ogham Village", "Kill The Executioner", "kill", "The Executioner", "", ["mandatory"], [])
a1_ids["ogham_village_03"] = add_step(1, "Ogham Village", "Free Leitis and proceed to Manor Ramparts", "travel", "The Manor Ramparts", "", ["mandatory"], [], {"type": "enter_area", "target_area": "The Manor Ramparts"})
a1_ids["manor_ramparts_01"] = add_step(1, "The Manor Ramparts", "Waypoint to town to talk to Leitis: Level 5 Uncut Skill Gem", "quest_reward", "Leitis", "Good time to turn in Una's Lute, Renley's Tools and do gear management", ["mandatory"], [])
a1_ids["manor_ramparts_02"] = add_step(1, "The Manor Ramparts", "(Optional) Cut down the Hanged Man at the Gallows: Uncut Support Gem", "loot", "Hanged Man", "You can click the Hanged Man from downstairs", ["optional"], [])
a1_ids["manor_ramparts_03"] = add_step(1, "The Manor Ramparts", "Enter Ogham Manor", "travel", "Ogham Manor", "", ["mandatory"], [], {"type": "enter_area", "target_area": "Ogham Manor"})
a1_ids["ogham_manor_01"] = add_step(1, "Ogham Manor", "(Permanent Buff) Defeat Candlemass: +20 Maximum Life", "kill", "Candlemass", "", ["permanent_buff"], [])
a1_ids["ogham_manor_02"] = add_step(1, "Ogham Manor", "Defeat Count Ogham", "kill", "Count Ogham", "", ["mandatory"], [])
a1_ids["clearfell_encampment_05"] = add_step(1, "The Clearfell Encampment", "Portal to Town and speak to The Hooded One to proceed to Act 2", "quest_reward", "The Hooded One", "", ["mandatory"], [])

a2_ids = {}
a2_ids["vastiri_outskirts_01"] = add_step(2, "Vastiri Outskirts", "Kill Rathbreaker", "kill", "Rathbreaker", "", ["mandatory"], [], {"type": "enter_area", "target_area": "Ardura Caravan"})
a2_ids["ardura_caravan_01"] = add_step(2, "Ardura Caravan", "Speak to Risu and Asala. Shop and gear up", "quest_reward", "", "Good time to shop and gear up", ["mandatory"], [])
a2_ids["ardura_caravan_02"] = add_step(2, "Ardura Caravan", "Use the Desert Map to take the caravan to Mawdun Quarry", "travel", "Mawdun Quarry", "", ["mandatory"], [], {"type": "enter_area", "target_area": "Mawdun Quarry"})
a2_ids["mawdun_quarry_01"] = add_step(2, "Mawdun Quarry", "Proceed through the zone and take the exit to Mawdun Mine", "travel", "Mawdun Mine", "", ["mandatory"], [], {"type": "enter_area", "target_area": "Mawdun Mine"})
a2_ids["mawdun_mine_01"] = add_step(2, "Mawdun Mine", "Kill Rudja, the Dread Engineer", "kill", "Rudja, the Dread Engineer", "", ["mandatory"], [])
a2_ids["mawdun_mine_02"] = add_step(2, "Mawdun Mine", "Free Risu from the cage and speak to them", "quest_reward", "Risu", "", ["mandatory"], [])
a2_ids["ardura_caravan_03"] = add_step(2, "Ardura Caravan", "Portal to Town and speak to Risu and Asala", "quest_reward", "", "", ["mandatory"], [])
a2_ids["ardura_caravan_04"] = add_step(2, "Ardura Caravan", "Use the Desert Map to travel to the Halani Gates", "travel", "The Halani Gates", "", ["mandatory"], [], {"type": "enter_area", "target_area": "The Halani Gates"})
a2_ids["halani_gates_01"] = add_step(2, "The Halani Gates", "Speak to Asala", "quest_reward", "Asala", "", ["mandatory"], [])
a2_ids["halani_gates_02"] = add_step(2, "The Halani Gates", "Travel to Traitor's Passage via the Desert Map", "travel", "Traitor's Passage", "", ["mandatory"], [], {"type": "enter_area", "target_area": "Traitor's Passage"})
a2_ids["traitors_passage_01"] = add_step(2, "Traitor's Passage", "(Ascendancy) Locate and open the Ancient Seal", "travel", "", "Located near a Lore Pillar", ["mandatory"], [])
a2_ids["traitors_passage_02"] = add_step(2, "Traitor's Passage", "Defeat Balbala, the Traitor: Balbala's Barya for Trial of Sekhemas", "kill", "Balbala, the Traitor", "", ["mandatory"], [])
a2_ids["halani_gates_03"] = add_step(2, "The Halani Gates", "Exit to the Halani Gates", "travel", "The Halani Gates", "", ["mandatory"], [], {"type": "enter_area", "target_area": "The Halani Gates"})
a2_ids["halani_gates_04"] = add_step(2, "The Halani Gates", "Summon Asala and proceed through the zone", "travel", "", "", ["mandatory"], [])
a2_ids["halani_gates_05"] = add_step(2, "The Halani Gates", "(Optional) Kill L'im the Impaler: Level 6 Uncut Skill Gem", "kill", "L'im the Impaler", "", ["optional"], [])
a2_ids["halani_gates_06"] = add_step(2, "The Halani Gates", "Defeat Jamanra", "kill", "Jamanra", "", ["mandatory"], [])
a2_ids["halani_gates_07"] = add_step(2, "The Halani Gates", "Run to the sandstorm until prompted to leave, then return to town", "travel", "Ardura Caravan", "", ["mandatory"], [], {"type": "enter_area", "target_area": "Ardura Caravan"})
a2_ids["ardura_caravan_05"] = add_step(2, "Ardura Caravan", "Speak to Zarka for a Level 7 Uncut Skill Gem", "quest_reward", "Zarka", "Start looking for Giant Life Flask and Giant Mana Flask upgrades if level 23", ["mandatory"], [])
a2_ids["trial_sekhemas_01"] = add_step(2, "Trial of the Sekhemas", "Travel to the Trial of the Sekhemas via the Desert Map", "travel", "Trial of the Sekhemas", "", ["mandatory"], [], {"type": "enter_area", "target_area": "Trial of the Sekhemas"})
a2_ids["trial_sekhemas_02"] = add_step(2, "Trial of the Sekhemas", "Speak to Balbala. Place Balbala's Barya and the Urn Relic in the altar", "quest_reward", "Balbala", "Use an Orb of Augmentation to enhance the Relic if you have one", ["mandatory"], [])
a2_ids["trial_sekhemas_03"] = add_step(2, "Trial of the Sekhemas", "Complete the first floor and defeat Rattlecage, the Earthbreaker", "kill", "Rattlecage, the Earthbreaker", "", ["mandatory"], [])
a2_ids["trial_sekhemas_04"] = add_step(2, "Trial of the Sekhemas", "Enter the Treasure Room. Touch the Altar of Ascendancy and loot chests", "quest_reward", "", "Purchase Relics from Balbala if able", ["mandatory"], [])
a2_ids["ardura_caravan_06"] = add_step(2, "Ardura Caravan", "Leave the Trial and return to Town", "travel", "Ardura Caravan", "", ["mandatory"], [], {"type": "enter_area", "target_area": "Ardura Caravan"})
a2_ids["keth_01"] = add_step(2, "Keth", "Travel to Keth via the Desert Map", "travel", "Keth", "", ["mandatory"], [], {"type": "enter_area", "target_area": "Keth"})
a2_ids["keth_02"] = add_step(2, "Keth", "Kill snake monsters until you find the Kabala Clan Relic", "kill", "", "", ["mandatory"], [])
a2_ids["keth_03"] = add_step(2, "Keth", "(Permanent Buff) Kill Kabala, Constrictor Queen: +2 Passives", "kill", "Kabala, Constrictor Queen", "Located in the middle of the zone, hiding underground in a pit with a checkpoint", ["permanent_buff"], [])
a2_ids["keth_04"] = add_step(2, "Keth", "(Optional) Enter and loot the Abandoned Shrine: Chest with a guaranteed Magic Amulet", "loot", "Abandoned Shrine", "", ["optional"], [])
a2_ids["keth_05"] = add_step(2, "Keth", "Exit to the Lost City", "travel", "The Lost City", "Located opposite side to the zone entrance, after a big bridge", ["mandatory"], [], {"type": "enter_area", "target_area": "The Lost City"})
a2_ids["lost_city_01"] = add_step(2, "The Lost City", "(Optional) The Golden Chest: Uncut Spirit Gem", "loot", "Golden Chest", "", ["optional"], [])
a2_ids["lost_city_02"] = add_step(2, "The Lost City", "(Optional) The Gilded Beetle: Random Ruby, Sapphire, or Emerald Jewel", "loot", "Gilded Beetle", "", ["optional"], [])
a2_ids["lost_city_03"] = add_step(2, "The Lost City", "Locate and use the exit to the Buried Shrines", "travel", "Buried Shrines", "", ["mandatory"], [], {"type": "enter_area", "target_area": "Buried Shrines"})
a2_ids["buried_shrines_01"] = add_step(2, "Buried Shrines", "(Optional) The Elemental Offering: Choose an Offering to obtain a Resistance Ring", "loot", "", "Choose Fire if Fire Resistance is low for the upcoming boss fight", ["optional"], [])
a2_ids["buried_shrines_02"] = add_step(2, "Buried Shrines", "(Optional) Open the Guarded Sarcophagus: Uncut Support Gem", "loot", "Guarded Sarcophagus", "", ["optional"], [])
a2_ids["buried_shrines_03"] = add_step(2, "Buried Shrines", "Defeat Azarian the Forsaken Son", "kill", "Azarian the Forsaken Son", "", ["mandatory"], [])
a2_ids["buried_shrines_04"] = add_step(2, "Buried Shrines", "Speak to the Water Goddess and claim The Essence of Water", "quest_reward", "", "", ["mandatory"], [])
a2_ids["ardura_caravan_07"] = add_step(2, "Ardura Caravan", "Portal to Town and speak to Zarka for an Uncut Support Gem", "quest_reward", "Zarka", "", ["mandatory"], [])
a2_ids["ardura_caravan_08"] = add_step(2, "Ardura Caravan", "Travel to the Mastodon Badlands via the Desert Map", "travel", "Mastodon Badlands", "", ["mandatory"], [], {"type": "enter_area", "target_area": "Mastodon Badlands"})
a2_ids["mastodon_01"] = add_step(2, "Mastodon Badlands", "(Optional) Loot the Shrine of Bones: Uncut Support Gem", "loot", "Shrine of Bones", "", ["optional"], [])
a2_ids["mastodon_02"] = add_step(2, "Mastodon Badlands", "Enter The Bone Pits", "travel", "The Bone Pits", "", ["mandatory"], [], {"type": "enter_area", "target_area": "The Bone Pits"})
a2_ids["bone_pits_01"] = add_step(2, "The Bone Pits", "Kill Monsters until you obtain the Sun Clan Relic", "kill", "", "", ["mandatory"], [])
a2_ids["bone_pits_02"] = add_step(2, "The Bone Pits", "Locate and defeat Iktab and Ekbab", "kill", "Iktab and Ekbab", "", ["mandatory"], [])
a2_ids["ardura_caravan_09"] = add_step(2, "Ardura Caravan", "Portal to Town. Travel to The Valley of Titans via the Desert Map", "travel", "The Valley of the Titans", "", ["mandatory"], [], {"type": "enter_area", "target_area": "The Valley of the Titans"})
a2_ids["valley_titans_01"] = add_step(2, "The Valley of the Titans", "Find and click the three ancient seals located by Titans to open the Titan Grotto", "travel", "", "", ["mandatory"], [])
a2_ids["valley_titans_02"] = add_step(2, "The Valley of the Titans", "(Permanent Buff) Locate the Relic Altar near the Waypoint and place the Sun and Kabala Clan Relics", "quest_reward", "", "Choose a buff (can be changed later)", ["permanent_buff"], [])
a2_ids["valley_titans_03"] = add_step(2, "The Valley of the Titans", "Enter the Titan Grotto", "travel", "The Titan Grotto", "", ["mandatory"], [], {"type": "enter_area", "target_area": "The Titan Grotto"})
a2_ids["titan_grotto_01"] = add_step(2, "The Titan Grotto", "Defeat Zalmarath, the Colossus", "kill", "Zalmarath, the Colossus", "", ["mandatory"], [])
a2_ids["ardura_caravan_10"] = add_step(2, "Ardura Caravan", "Portal to Town and speak to Zarka: Uncut Support Gem", "quest_reward", "Zarka", "", ["mandatory"], [])
a2_ids["halani_gates_08"] = add_step(2, "The Halani Gates", "Travel to the Halani Gates. Use The Horn of the Vastiri at the front of the Caravan", "travel", "The Halani Gates", "", ["mandatory"], [], {"type": "enter_area", "target_area": "The Halani Gates"})
a2_ids["halani_gates_09"] = add_step(2, "The Halani Gates", "Speak to Asala. Travel to Deshar via Desert Map", "travel", "Deshar", "", ["mandatory"], [], {"type": "enter_area", "target_area": "Deshar"})
a2_ids["deshar_01"] = add_step(2, "Deshar", "(Permanent Buff) Locate the Fallen Dekhara and take the Final Letter", "loot", "", "Check the base of each round building for the Dekhara", ["permanent_buff"], [])
a2_ids["deshar_02"] = add_step(2, "Deshar", "Exit to the Path of Mourning", "travel", "The Path of Mourning", "", ["mandatory"], [], {"type": "enter_area", "target_area": "The Path of Mourning"})
a2_ids["path_mourning_01"] = add_step(2, "The Path of Mourning", "Waypoint to Town. Deliver Final Letter to Shambrin: +2 Passive Points", "quest_reward", "Shambrin", "", ["mandatory"], [])
a2_ids["path_mourning_02"] = add_step(2, "The Path of Mourning", "(Optional) Shifting Vases event: Uncut Support Gem", "loot", "Shifting Vases", "", ["optional"], [])
a2_ids["path_mourning_03"] = add_step(2, "The Path of Mourning", "Exit to The Spires of Deshar", "travel", "The Spires of Deshar", "", ["mandatory"], [], {"type": "enter_area", "target_area": "The Spires of Deshar"})
a2_ids["spires_deshar_01"] = add_step(2, "The Spires of Deshar", "(Permanent Buff) Activate the Sisters of Garukhan shrine: +10% Lightning Resistance", "quest_reward", "", "", ["permanent_buff"], [])
a2_ids["spires_deshar_02"] = add_step(2, "The Spires of Deshar", "Defeat Tor Gul, the Defiler", "kill", "Tor Gul, the Defiler", "", ["mandatory"], [])
a2_ids["ardura_caravan_11"] = add_step(2, "Ardura Caravan", "Portal to Town. Speak to Asala", "quest_reward", "Asala", "Vendors can sell level 30 key items around here", ["mandatory"], [])
a2_ids["dreadnought_01"] = add_step(2, "The Dreadnought", "Travel to The Dreadnought via Desert Map", "travel", "The Dreadnought", "", ["mandatory"], [], {"type": "enter_area", "target_area": "The Dreadnought"})
a2_ids["dreadnought_02"] = add_step(2, "The Dreadnought", "Fight your way to the Dreadnought Vanguard exit", "travel", "The Dreadnought Vanguard", "Final checkpoint has multiple blue monsters you can farm", ["mandatory"], [], {"type": "enter_area", "target_area": "The Dreadnought Vanguard"})
a2_ids["dreadnought_vanguard_01"] = add_step(2, "The Dreadnought Vanguard", "Locate and defeat Jamanra, the Abomination", "kill", "Jamanra, the Abomination", "", ["mandatory"], [])
a2_ids["ardura_caravan_12"] = add_step(2, "Ardura Caravan", "Speak to the Hooded One and Asala. Travel to Sandswept Marsh in Act 3", "travel", "Sandswept Marsh", "", ["mandatory"], [], {"type": "enter_area", "target_area": "Sandswept Marsh"})

a3_ids = {}
a3_ids["sandswept_01"] = add_step(3, "Sandswept Marsh", "(Optional) Kill Rootdredge: Level 9 Uncut Skill Gem", "kill", "Rootdredge", "", ["optional"], [])
a3_ids["sandswept_02"] = add_step(3, "Sandswept Marsh", "(Optional) Loot Corpse at Hanging Tree: Random Magic Ring", "loot", "Hanging Tree", "", ["optional"], [])
a3_ids["sandswept_03"] = add_step(3, "Sandswept Marsh", "(Optional - Highly Recommended) Kill Rare Oroks and Loot Basket in Orok Campsite: Lesser Jeweller's Orb", "loot", "Orok Campsite", "", ["optional", "recommended"], [])
a3_ids["sandswept_04"] = add_step(3, "Sandswept Marsh", "Exit to Ziggurat Encampment (Town)", "travel", "Ziggurat Encampment", "", ["mandatory"], [], {"type": "enter_area", "target_area": "Ziggurat Encampment"})
a3_ids["ziggurat_01"] = add_step(3, "Ziggurat Encampment", "Speak to Alva and Oswald. Hunt for Flask upgrades and 20% Movespeed Boots", "quest_reward", "", "Good opportunity to shop", ["mandatory"], [])
a3_ids["ziggurat_02"] = add_step(3, "Ziggurat Encampment", "Exit to the Jungle Ruins", "travel", "Jungle Ruins", "Located near the top of town", ["mandatory"], [], {"type": "enter_area", "target_area": "Jungle Ruins"})
a3_ids["jungle_ruins_01"] = add_step(3, "Jungle Ruins", "Defeat Silverfist: +2 Passives", "kill", "Silverfist", "Located within stone ruins", ["permanent_buff"], [])
a3_ids["jungle_ruins_02"] = add_step(3, "Jungle Ruins", "(Optional) Summon the NPC to the Jungle Grave: Rare Belt", "loot", "Jungle Grave", "Likely only worth doing if your belt is very bad", ["optional"], [])
a3_ids["jungle_ruins_03"] = add_step(3, "Jungle Ruins", "(Optional) Loot the white chest in Gwendolyn Albright's Troubled Campsite", "loot", "", "Gwendolyn sells high quality armour, check for upgrades", ["optional"], [])
a3_ids["jungle_ruins_04"] = add_step(3, "Jungle Ruins", "Activate the Waypoint and Enter the Venom Crypts", "travel", "The Venom Crypts", "", ["mandatory"], [], {"type": "enter_area", "target_area": "The Venom Crypts"})
a3_ids["venom_crypts_01"] = add_step(3, "The Venom Crypts", "Locate the Den of the Serpent Priestess and Loot the Corpse-snake Venom", "loot", "Corpse-snake Venom", "", ["mandatory"], [])
a3_ids["ziggurat_03"] = add_step(3, "Ziggurat Encampment", "Portal to Town. Give the Corpse-snake Venom to Servi", "quest_reward", "Servi", "Choose a permanent buff reward. WARNING: This cannot be changed later!", ["mandatory"], [])
a3_ids["infested_barrens_01"] = add_step(3, "Infested Barrens", "Waypoint to Jungle Ruins. Take the exit to Infested Barrens", "travel", "Infested Barrens", "Located on one of the outer zone edges (typically opposite the exit to town)", ["mandatory"], [], {"type": "enter_area", "target_area": "Infested Barrens"})
a3_ids["infested_barrens_02"] = add_step(3, "Infested Barrens", "Activate the Waypoint and summon Alva", "quest_reward", "Alva", "Look for a stone platform near the water with the waypoint and a checkpoint nearby", ["mandatory"], [])
a3_ids["infested_barrens_03"] = add_step(3, "Infested Barrens", "(Optional) Loot the white chest in Sebastian Carroway's Troubled Campsite: Rare Boots", "loot", "", "This vendor also sells higher-quality weapons", ["optional"], [])
a3_ids["infested_barrens_04"] = add_step(3, "Infested Barrens", "Hug the outside wall to locate the exit to the Azak Bog", "travel", "The Azak Bog", "", ["mandatory"], [], {"type": "enter_area", "target_area": "The Azak Bog"})
a3_ids["azak_bog_01"] = add_step(3, "The Azak Bog", "Summon and speak to Servi, if needed", "quest_reward", "Servi", "", ["optional"], [])
a3_ids["azak_bog_02"] = add_step(3, "The Azak Bog", "(Optional) Complete the Flameskin Ritual for temporary boost to Fire Resistance and Rarity", "quest_reward", "", "Only needed if your Fire Resistance is very low (below 30-40%)", ["optional"], [])
a3_ids["azak_bog_03"] = add_step(3, "The Azak Bog", "(Permanent Buff) Defeat Ignagduk, the Bog Witch: +30 Spirit and Uncut Spirit Gem", "kill", "Ignagduk, the Bog Witch", "", ["permanent_buff"], [])
a3_ids["ziggurat_04"] = add_step(3, "Ziggurat Encampment", "Portal to town. Speak to Servi to obtain your choice of Charm", "quest_reward", "Servi", "Thawing is recommended if you don't have one already, otherwise Antidote", ["mandatory"], [])
a3_ids["chimeral_wetlands_01"] = add_step(3, "Chimeral Wetlands", "Take the Waypoint to Infested Barrens, hug the wall until you locate the exit to Chimeral Wetlands", "travel", "Chimeral Wetlands", "", ["mandatory"], [], {"type": "enter_area", "target_area": "Chimeral Wetlands"})
a3_ids["chimeral_wetlands_02"] = add_step(3, "Chimeral Wetlands", "Enter The Temple of Chaos and activate the waypoint, then return to Chimeral Wetlands", "travel", "The Temple of Chaos", "", ["mandatory"], [], {"type": "enter_area", "target_area": "The Temple of Chaos"})
a3_ids["chimeral_wetlands_03"] = add_step(3, "Chimeral Wetlands", "Defeat Xyclucian, the Chimera: Obtain Chimeral Inscribed Ultimatum for Ascendancy", "kill", "Xyclucian, the Chimera", "", ["mandatory"], [])
a3_ids["chimeral_wetlands_04"] = add_step(3, "Chimeral Wetlands", "Exit to Jiquani's Machinarium", "travel", "Jiquani's Machinarium", "", ["mandatory"], [], {"type": "enter_area", "target_area": "Jiquani's Machinarium"})
a3_ids["jiquani_mach_01"] = add_step(3, "Jiquani's Machinarium", "Locate a Small Soul Core in one of the two entrance offshoot rooms", "loot", "", "", ["mandatory"], [])
a3_ids["jiquani_mach_02"] = add_step(3, "Jiquani's Machinarium", "Use Soul Core to open the door. Locate an additional Small Soul Core", "travel", "", "", ["mandatory"], [])
a3_ids["jiquani_mach_03"] = add_step(3, "Jiquani's Machinarium", "(Permanent Buff) Open the door and kill Blackjaw, the Remnant: +10% Fire Resistance", "kill", "Blackjaw, the Remnant", "", ["permanent_buff"], [])
a3_ids["jiquani_mach_04"] = add_step(3, "Jiquani's Machinarium", "(Optional - Low Priority) use a third Soul Core to unlock and loot the Treasure Vault", "loot", "Treasure Vault", "", ["optional"], [])
a3_ids["jiquani_mach_05"] = add_step(3, "Jiquani's Machinarium", "Obtain another Small Soul Core. Use Soul Core to open the exit to Jiquani's Sanctum", "travel", "Jiquani's Sanctum", "", ["mandatory"], [], {"type": "enter_area", "target_area": "Jiquani's Sanctum"})
a3_ids["jiquani_sanctum_01"] = add_step(3, "Jiquani's Sanctum", "Head to the left or right generator and look for a Medium Soul Core", "loot", "", "", ["mandatory"], [])
a3_ids["jiquani_sanctum_02"] = add_step(3, "Jiquani's Sanctum", "Place Medium Soul Core inside generator", "travel", "", "", ["mandatory"], [])
a3_ids["jiquani_sanctum_03"] = add_step(3, "Jiquani's Sanctum", "Cut through the middle of the zone to the second generator, looking for another Medium Soul Core", "loot", "", "", ["mandatory"], [])
a3_ids["jiquani_sanctum_04"] = add_step(3, "Jiquani's Sanctum", "Defeat Jiquani", "kill", "Jiquani", "", ["mandatory"], [])
a3_ids["ziggurat_05"] = add_step(3, "Ziggurat Encampment", "Portal to Town. Speak to Alva and Oswald", "quest_reward", "", "", ["mandatory"], [])
a3_ids["ziggurat_06"] = add_step(3, "Ziggurat Encampment", "Exit to The Drowned City", "travel", "The Drowned City", "", ["mandatory"], [], {"type": "enter_area", "target_area": "The Drowned City"})
a3_ids["drowned_city_01"] = add_step(3, "The Drowned City", "(Optional) Kill The Devourer of Souls: Uncut Spirit Gem", "kill", "The Devourer of Souls", "", ["optional"], [])
a3_ids["drowned_city_02"] = add_step(3, "The Drowned City", "Enter The Molten Vault", "travel", "The Molten Vault", "", ["mandatory"], [], {"type": "enter_area", "target_area": "The Molten Vault"})
a3_ids["molten_vault_01"] = add_step(3, "The Molten Vault", "Defeat The Molten King", "kill", "The Molten King", "", ["mandatory"], [])
a3_ids["drowned_city_03"] = add_step(3, "The Drowned City", "Return to The Drowned City. Enter The Apex of Filth", "travel", "The Apex of Filth", "", ["mandatory"], [], {"type": "enter_area", "target_area": "The Apex of Filth"})
a3_ids["apex_filth_01"] = add_step(3, "The Apex of Filth", "Defeat The Filthlord", "kill", "The Filthlord", "", ["mandatory"], [])
a3_ids["ziggurat_07"] = add_step(3, "Ziggurat Encampment", "Portal to Town and speak to The Hooded One to proceed to Act 4", "quest_reward", "The Hooded One", "", ["mandatory"], [])

a4_ids = {}
a4_ids["kedge_bay_01"] = add_step(4, "Kedge Bay", "Enter Kedge Bay (Passive Points Island)", "travel", "Kedge Bay", "", ["mandatory"], [], {"type": "enter_area", "target_area": "Kedge Bay"})
a4_ids["kedge_bay_02"] = add_step(4, "Kedge Bay", "Complete the puzzles and claim your +2 Passive Points", "quest_reward", "", "", ["permanent_buff"], [])
a4_ids["isle_kin_01"] = add_step(4, "Isle of Kin", "Travel to Isle of Kin", "travel", "Isle of Kin", "", ["mandatory"], [], {"type": "enter_area", "target_area": "Isle of Kin"})
a4_ids["volcanic_warrens_01"] = add_step(4, "Volcanic Warrens", "Enter Volcanic Warrens", "travel", "Volcanic Warrens", "", ["mandatory"], [], {"type": "enter_area", "target_area": "Volcanic Warrens"})
a4_ids["whakapanu_01"] = add_step(4, "Whakapanu Island", "Travel to Whakapanu Island", "travel", "Whakapanu Island", "", ["mandatory"], [], {"type": "enter_area", "target_area": "Whakapanu Island"})
a4_ids["singing_caverns_01"] = add_step(4, "Singing Caverns", "Enter Singing Caverns", "travel", "Singing Caverns", "", ["mandatory"], [], {"type": "enter_area", "target_area": "Singing Caverns"})
a4_ids["abandoned_prison_01"] = add_step(4, "Abandoned Prison", "Travel to Abandoned Prison", "travel", "Abandoned Prison", "", ["mandatory"], [], {"type": "enter_area", "target_area": "Abandoned Prison"})
a4_ids["solitary_confinement_01"] = add_step(4, "Solitary Confinement", "Enter Solitary Confinement", "travel", "Solitary Confinement", "", ["mandatory"], [], {"type": "enter_area", "target_area": "Solitary Confinement"})
a4_ids["shrike_island_01"] = add_step(4, "Shrike Island", "Travel to Shrike Island. Get Matiki", "travel", "Shrike Island", "", ["mandatory"], [], {"type": "enter_area", "target_area": "Shrike Island"})
a4_ids["eye_hinekora_01"] = add_step(4, "Eye of Hinekora", "Travel to Eye of Hinekora / Halls of the Dead", "travel", "Eye of Hinekora", "", ["mandatory"], [], {"type": "enter_area", "target_area": "Eye of Hinekora"})
a4_ids["arastas_01"] = add_step(4, "Arastas", "Travel to Arastas / The Excavation", "travel", "Arastas", "", ["mandatory"], [], {"type": "enter_area", "target_area": "Arastas"})
a4_ids["excavation_01"] = add_step(4, "The Excavation", "Enter The Excavation", "travel", "The Excavation", "", ["mandatory"], [], {"type": "enter_area", "target_area": "The Excavation"})
a4_ids["ngakanu_01"] = add_step(4, "Ngakanu", "Travel to Ngakanu / Heart of the Tribe", "travel", "Ngakanu", "", ["mandatory"], [], {"type": "enter_area", "target_area": "Ngakanu"})
a4_ids["heart_tribe_01"] = add_step(4, "Heart of the Tribe", "Enter Heart of the Tribe and complete Act 4", "travel", "Heart of the Tribe", "", ["mandatory"], [], {"type": "enter_area", "target_area": "Heart of the Tribe"})

# TODO: Act 5 - Add zone data
a5_ids = {}

# TODO: Act 6 - Add zone data
a6_ids = {}

# TODO: Act 7 - Add zone data
a7_ids = {}

with open("data/guides/poe2_campaign.json", "w") as f:
    json.dump(POE2_GUIDE, f, indent=2)

print(f"Guide generated with {len(POE2_GUIDE['steps'])} steps across {len(POE2_GUIDE['acts'])} acts")
