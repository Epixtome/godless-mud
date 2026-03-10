"""
logic/core/utils/status_definitions.py
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
SOFT_DEBUFFS = {"wet", "cold", "muddy", "bleed", "corroded", "blind", "panting"}

CORE_STATUS_DEFINITIONS = {
    "prone": {
        "name": "Prone",
        "blocks": ["movement", "combat", "skills"],
        "description": "Knocked to the ground. You must 'stand' to act.",
        "metadata": {"is_debuff": True}
    },
    "panting": {
        "name": "Panting",
        "blocks": ["combat", "skills"],
        "description": "Gasping for breath from over-exertion.",
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
        "blocks": ["combat"],
        "description": "Reeling from a heavy blow. Cannot attack.",
        "metadata": {"is_debuff": True}
    },
    "overheated": {
        "name": "Overheated",
        "blocks": ["movement", "combat"],
        "metadata": {"is_debuff": True}
    },
    "turtle_stance": {
        "name": "Turtle Stance",
        "description": "A defensive stance granting immunity to knockdowns.",
        "metadata": {"immune_to": ["prone", "knockback"]}
    },
    "wet": {
        "name": "Wet",
        "description": "Soaked with water. Lightning damage may be increased.",
        "metadata": {"is_debuff": True}
    },
    "atrophy": {
        "name": "Atrophy",
        "description": "Your muscles waste away. Stamina regeneration is disabled.",
        "blocks": ["stamina_regen"],
        "metadata": {"is_debuff": True}
    }
}
