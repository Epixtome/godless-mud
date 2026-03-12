"""
logic/systems/status/definitions.py
Static data for core status effects.
"""

STATUS_MAP = {
    'hidden': 'concealed',
    'sneaking': 'concealed',
    'stealth': 'concealed'
}

# Status Hierarchy
CRITICAL_STATES = {"prone", "off_balance", "jarred", "stun"}
HARD_DEBUFFS = {"shocked", "overheated", "webbed", "frozen", "silence", "disarmed"}
SOFT_DEBUFFS = {"wet", "cold", "muddy", "bleed", "corroded", "blind", "panting", "poison", "burn"}

CORE_STATUS_DEFINITIONS = {
    "prone": {
        "name": "Prone",
        "blocks": ["movement", "combat", "skills"],
        "description": "Knocked to the ground. You are critically exposed (1.5x damage) and must 'stand' before you can act again.",
        "metadata": {"is_debuff": True}
    },
    "off_balance": {
        "name": "Off-Balance",
        "blocks": ["skills"],
        "description": "Your posture is shattered. You are critically exposed (1.5x damage) and cannot use complex maneuvers or skills.",
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
    "overheated": {
        "name": "Overheated",
        "blocks": ["movement", "combat"],
        "metadata": {"is_debuff": True}
    },
    "crane_stance": {
        "name": "Crane Stance",
        "description": "A fluid, defensive stance. Increases Wisdom and Defense, making the Monk harder to hit and more resilient to magical effects.",
        "group": "stance",
        "metadata": {"is_buff": True}
    },
    "turtle_stance": {
        "name": "Turtle Stance",
        "description": "A low-profile, grounded stance. Grants immunity to knockdowns and reduces physical damage taken by 15%.",
        "group": "stance",
        "metadata": {"immune_to": ["prone", "knockback"], "mitigation_mult": 0.85}
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
        "metadata": {"is_debuff": True}
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
