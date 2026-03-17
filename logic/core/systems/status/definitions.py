"""
logic/systems/status/definitions.py
Static data for core status effects.
"""

STATUS_MAP = {
    'hidden': 'concealed',
    'sneaking': 'concealed',
    'stealth': 'concealed',
    'stun': 'stunned'
}

# Status Hierarchy
CRITICAL_STATES = {"prone", "off_balance", "jarred", "stun", "stunned", "incapacitated", "shattered_mind", "exposed", "pinned"}
HARD_DEBUFFS = {"shocked", "overheated", "webbed", "frozen", "silence", "disarmed", "immobilized", "feared"}
SOFT_DEBUFFS = {"wet", "cold", "muddy", "bleed", "corroded", "blinded", "panting", "poison", "burn", "marked", "staggered"}

CORE_STATUS_DEFINITIONS = {
    "prone": {
        "name": "Prone",
        "blocks": ["movement", "combat", "skills"],
        "description": "Knocked to the ground. You are critically exposed (1.5x damage) and must 'stand' before you can act again.",
        "metadata": {"is_debuff": True, "damage_taken_mult": 1.5}
    },
    "pinned": {
        "name": "Pinned",
        "blocks": ["movement", "skills"],
        "description": "Held firmly in place. You cannot move or use physical skills. Taking damage while pinned may cause [Prone].",
        "metadata": {"is_debuff": True}
    },
    "immobilized": {
        "name": "Immobilized",
        "blocks": ["movement"],
        "description": "Your feet are anchored to the ground. You cannot move, but you can still fight and use skills.",
        "metadata": {"is_debuff": True}
    },
    "off_balance": {
        "name": "Off-Balance",
        "blocks": ["skills", "reaction"],
        "description": "Your posture is shattered. You are critically exposed (1.25x damage) and cannot use reactions or complex maneuvers.",
        "metadata": {"is_debuff": True, "damage_taken_mult": 1.25}
    },
    "exposed": {
        "name": "Exposed",
        "blocks": [],
        "description": "Your physical guard has been bypassed. The next hit taken is a guaranteed Critical.",
        "metadata": {"is_debuff": True, "guaranteed_crit_taken": True}
    },
    "staggered": {
        "name": "Staggered",
        "blocks": ["skills"],
        "description": "Momentarily reeling from a blow. Current actions are interrupted.",
        "metadata": {"is_debuff": True}
    },
    "marked": {
        "name": "Marked",
        "blocks": [],
        "description": "Tracked and targeted. You are visible through fog/stealth, and ranged attacks deal 20% more damage to you.",
        "metadata": {"is_debuff": True, "ranged_damage_bonus": 0.2}
    },
    "shocked": {
        "name": "Shocked",
        "blocks": ["skills"],
        "description": "Electrical currents course through your body, disrupting your ability to perform complex skills.",
        "metadata": {"is_debuff": True}
    },
    "panting": {
        "name": "Panting",
        "blocks": ["skills", "movement"],
        "description": "Gasping for breath from over-exertion. You are too winded to use complex skills or move efficiently, but you can still defend yourself.",
        "metadata": {"is_debuff": True}
    },
    "exhausted": {
        "name": "Exhausted",
        "blocks": [],
        "description": "Movement is significantly slowed due to over-exertion.",
        "metadata": {"is_debuff": True}
    },
    "stalled": {
        "name": "Stalled",
        "blocks": ["movement"],
        "description": "Momentarily stopped by physical friction.",
        "metadata": {"is_debuff": True}
    },
    "dazed": {
        "name": "Dazed",
        "blocks": ["combat", "skills"],
        "description": "Reeling from a heavy blow. Cannot attack.",
        "metadata": {"is_debuff": True}
    },
    "stunned": {
        "name": "Stunned",
        "blocks": ["movement", "combat", "skills"],
        "description": "Completely incapacitated. You cannot move, fight, or use skills.",
        "metadata": {"is_debuff": True}
    },
    "stun": {
        "name": "Stunned",
        "blocks": ["movement", "combat", "skills"],
        "description": "Completely incapacitated. You cannot move, fight, or use skills.",
        "metadata": {"is_debuff": True}
    },
    "overheated": {
        "name": "Overheated",
        "blocks": ["movement", "combat"],
        "metadata": {"is_debuff": True}
    },
    "crane_stance": {
        "name": "Crane Stance",
        "description": "The Wind. A fluid, defensive stance. Doubled Stamina regeneration and increased Evasion.",
        "group": "stance",
        "metadata": {"is_buff": True, "stamina_regen_mult": 2.0, "display_in_prompt": False}
    },
    "turtle_stance": {
        "name": "Turtle Stance",
        "description": "The Mountain. A low-profile, grounded stance. Grants immunity to [Prone], reduces incoming damage, and regenerates Balance.",
        "group": "stance",
        "metadata": {"is_buff": True, "immune_to": ["prone", "knockback"], "mitigation_mult": 0.85, "balance_regen_bonus": 20, "display_in_prompt": False}
    },
    "tiger_stance": {
        "name": "Tiger Stance",
        "description": "The Breaker. An aggressive, high-impact stance. Increased damage and Crit chance, but double Stamina costs.",
        "group": "stance",
        "metadata": {"is_buff": True, "damage_mult": 1.25, "crit_chance_bonus": 0.15, "stamina_cost_mult": 2.0, "display_in_prompt": False}
    },
    "mantis_stance": {
        "name": "Mantis Stance",
        "description": "The Trap. A precise, opportunistic stance. Counter-attacks when hit, but disables all resource regeneration.",
        "group": "stance",
        "metadata": {"is_buff": True, "counter_chance": 1.0, "regen_suppressed": True, "display_in_prompt": False}
    },
    "predator_flow": {
        "name": "Predator Flow",
        "description": "Tiger flow: Your next strike is a guaranteed critical hit.",
        "metadata": {"is_buff": True, "display_in_prompt": False}
    },
    "water_flow": {
        "name": "Water Flow",
        "description": "Crane flow: Your heightened perception allows you to automatically evade the next attack.",
        "metadata": {"is_buff": True, "display_in_prompt": False}
    },
    "stone_flow": {
        "name": "Stone Flow",
        "description": "Turtle flow: Instant restoration of physical composure (Balance).",
        "metadata": {"is_buff": True, "display_in_prompt": False}
    },
    "razor_flow": {
        "name": "Razor Flow",
        "description": "Mantis flow: Your next attack will slice deep, causing your target to bleed.",
        "metadata": {"is_buff": True, "display_in_prompt": False}
    },
    "wet": {
        "name": "Wet",
        "description": "Soaked with water. Increases Lightning damage taken and makes you susceptible to Freezing.",
        "metadata": {"is_debuff": True}
    },
    "atrophy": {
        "name": "Atrophy",
        "description": "Your muscles waste away. Stamina regeneration is disabled.",
        "blocks": ["stamina_regen"],
        "metadata": {"is_debuff": True}
    },
    "bleed": {
        "name": "Bleeding",
        "description": "You are losing blood rapidly.",
        "metadata": {"is_debuff": True}
    },
    "burn": {
        "name": "Burning",
        "description": "You are on fire, taking steady damage.",
        "metadata": {"is_debuff": True}
    },
    "poison": {
        "name": "Poisoned",
        "description": "Toxic venom saps your vitality.",
        "metadata": {"is_debuff": True}
    },
    "magic_shield": {
        "name": "Magic Shield",
        "description": "An arcane barrier redirects incoming damage to your Concentration.",
        "metadata": {"is_buff": True}
    },
    "concealed": {
        "name": "Concealed",
        "description": "Hidden from sight. Your next attack will strike from the shadows.",
        "metadata": {"is_buff": True}
    },
    "dualcast": {
        "name": "Dualcast",
        "description": "Focusing your mind to cast your next spell twice.",
        "metadata": {"is_buff": True}
    },
    "braced": {
        "name": "Braced",
        "description": "Tightly holding your position, reducing physical damage taken.",
        "metadata": {"is_buff": True}
    },
    "shield_of_faith": {
        "name": "Shield of Faith",
        "description": "Divine protection wards off harm.",
        "metadata": {"is_buff": True}
    },
    "sanctified": {
        "name": "Sanctified",
        "description": "Blessed ground empowers your spirit.",
        "metadata": {"is_buff": True}
    },
    "plague": {
        "name": "Plague",
        "description": "A virulent sickness saps your strength.",
        "metadata": {"is_debuff": True}
    },
    "fear": {
        "name": "Fear",
        "description": "Paralyzing dread grips your heart.",
        "blocks": ["combat", "skills"],
        "metadata": {"is_debuff": True}
    },
    "curse": {
        "name": "Cursed",
        "description": "Dark energies hinder your fate.",
        "metadata": {"is_debuff": True}
    },
    "hunger": {
        "name": "Hunger",
        "description": "An unnatural void gnaws at your essence.",
        "metadata": {"is_debuff": True}
    },
    "malediction": {
        "name": "Malediction",
        "description": "A heavy doom weighs upon you.",
        "metadata": {"is_debuff": True}
    },
    "frozen": {
        "name": "Frozen",
        "description": "Encased in absolute zero ice. You cannot move or act.",
        "blocks": ["movement", "combat", "skills"],
        "metadata": {"is_debuff": True}
    },
    "blinded": {
        "name": "Blinded",
        "description": "Your vision is obscured by darkness or debris.",
        "metadata": {"is_debuff": True, "accuracy_penalty": 90}
    },
    "silenced": {
        "name": "Silenced",
        "description": "You cannot utter spells or verbal commands.",
        "blocks": ["skills"],
        "metadata": {"is_debuff": True}
    },
    "confused": {
        "name": "Confused",
        "description": "Your mind is clouded and wandering.",
        "blocks": ["skills"],
        "metadata": {"is_debuff": True}
    },
    "staggered": {
        "name": "Staggered",
        "description": "Momentarily off-balance. You cannot use complex skills or maneuvers.",
        "blocks": ["skills"],
        "metadata": {"is_debuff": True}
    },
    "bloodrage": {
        "name": "Bloodrage",
        "description": "YOUR BLOOD BOILS! You are immune to crowd control and gain 20% damage mitigation.",
        "metadata": {
            "is_buff": True, 
            "immune_to": ["prone", "stunned", "stun", "dazed", "fear", "off_balance"],
            "mitigation_mult": 0.80
        }
    },
    # Environmental / Room Effects
    "bloodspattered": {
        "name": "Bloodspattered",
        "description": "The floor is slick with fresh blood.",
        "metadata": {"is_environmental": True, "movement_slip_chance": 0.05}
    },
    "blighted": {
        "name": "Blighted",
        "description": "The very air in this place feels toxic and necrotic.",
        "metadata": {"is_environmental": True, "healing_reduction": 0.5}
    },
    "frozen_ground": {
        "name": "Frozen Ground",
        "description": "The ground is covered in a dangerous layer of magical ice.",
        "metadata": {"is_environmental": True, "traversal_penalty": 2}
    }
}
