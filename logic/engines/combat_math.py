"""
Handles pure mathematical calculations for combat.
Extracts damage formulas, friction scaling, and text generation logic
to keep the main processor clean.
"""
from logic.constants import Tags
from logic.engines import blessings_engine
from logic.engines import combat_engine
from models import Player

def calculate_base_damage(attacker, target, blessing=None):
    """
    Calculates the raw base damage before events and modifiers.
    Routes to the appropriate engine based on entity type and action.
    """
    raw_damage = 0
    if isinstance(attacker, Player):
        if blessing:
            raw_damage = blessings_engine.calculate_power(blessing, attacker, target)
        else:
            raw_damage = combat_engine.calculate_player_damage(attacker, target)
    else:
        # Monster / Mob
        if blessing:
            raw_damage = blessings_engine.calculate_power(blessing, attacker, target)
        else:
            raw_damage = combat_engine.calculate_mob_damage(attacker, target)
            
    return int(raw_damage)


def get_attack_verb(damage_percent):
    """
    Determines the verb used in combat messages based on damage severity.
    """
    if damage_percent >= 0.50:
        return "OBLITERATE"
    elif damage_percent >= 0.20:
        return "decimate"
    return "strike"
