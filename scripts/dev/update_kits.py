import json

kit_path = r"c:\Users\Chris\antigravity\Godless\data\kits.json"
with open(kit_path, 'r') as f:
    data = json.load(f)

new_classes = {
    "chemist": {
        "name": "Chemist",
        "description": "The Mixmaster. Uses alchemy and concoctions to buff allies or dissolve foes through chemical reactions.",
        "gear": ["alchemists_flask", "heavy_apron"],
        "blessings": ["toss_philter", "catalyze", "acid_flask", "healing_mist", "smoke_screen", "explosive_mix", "reagent_dash", "ultimate_compound", "chemist_physiology"],
        "identity_tags": ["magic", "alchemy"],
        "resources": ["stamina", "reagent_pips"],
        "axes": ["utility", "elemental"],
        "version": "7.2"
    },
    "dancer": {
        "name": "Dancer",
        "description": "The Rhythm Blade. Weaves martial strikes into intricate dances to buff allies and confuse enemies with lethal tempo.",
        "gear": ["martial_fans", "dancing_garb"],
        "blessings": ["step_strike", "rhythmical_motion", "bladed_waltz", "pirouette_slam", "defensive_dance", "enchanting_step", "rhythmic_dash", "finale_encore", "dancer_physiology"],
        "identity_tags": ["martial", "speed"],
        "resources": ["stamina", "rhythm"],
        "axes": ["speed", "utility"],
        "version": "7.2"
    },
    "summoner": {
        "name": "Summoner",
        "description": "The Caller. Bridges the veil to summon powerful entities to fight on their behalf.",
        "gear": ["summoners_staff", "ritual_robes"],
        "blessings": ["bind_spirit", "call_imp", "unleash_eidolon", "synergy_strike", "spirit_shield", "guardian_summon", "veil_step", "grand_invocation", "summoner_physiology"],
        "identity_tags": ["magic", "summoning"],
        "resources": ["stamina", "aether_pips"],
        "axes": ["utility", "endurance"],
        "version": "7.2"
    },
    "puppet_master": {
        "name": "Puppet Master",
        "description": "The Strings of Fate. Commands mechanical or magical puppets to dominate the battlefield through proxy control.",
        "gear": ["control_strings", "heavy_cloak"],
        "blessings": ["puppet_strike", "string_pull", "synchronize", "overdrive", "iron_guard", "marionette_dodge", "thread_dash", "grand_puppeteer", "puppet_master_physiology"],
        "identity_tags": ["magic", "tech"],
        "resources": ["stamina", "control_pips"],
        "axes": ["utility", "position"],
        "version": "7.2"
    },
    "machinist": {
        "name": "Machinist",
        "description": "The Gadgeteer. Uses firearms and mechanical drones to control distance and apply constant ballistic pressure.",
        "gear": ["auto_pistol", "tech_goggles", "tool_belt"],
        "blessings": ["shot_burst", "tech_mark", "drone_strike", "ballistic_barrage", "auto_barrier", "turret_setup", "rocket_jump", "satellite_beam", "machinist_physiology"],
        "identity_tags": ["martial", "gun", "tech"],
        "resources": ["stamina", "ammunition"],
        "axes": ["position", "lethality"],
        "version": "7.2"
    }
}

data.update(new_classes)

with open(kit_path, 'w') as f:
    json.dump(data, f, indent=4)
