"""
logic/engines/blessings/math/reactions.py
Evaluates defender reactions (Parry, Block, Phase Shift).
"""
import logging
from logic.core import effects, resources

logger = logging.getLogger("GodlessMUD")

def resolve_reaction(attacker, target, attack_tags):
    """
    [V6.0] Evaluates if a defender's active reaction (Parry/Block) succeeds.
    Returns: (bool success, str feedback_message, dict result_mods)
    """
    # 1. Check for active Reaction Statuses
    t_effects = getattr(target, 'status_effects', {})
    if not t_effects: return False, "", {}

    from logic.core.utils import combat_logic
    a_weight = combat_logic.get_weight_class(attacker)
    t_weight = combat_logic.get_weight_class(target)
    
    # --- MONK: FLOW PARRY ---
    if "flow_mastery" in t_effects:
        if "weight" in attack_tags or "sweep" in attack_tags:
            return False, f"The weight of {attacker.name}'s strike is too great to parry!", {}
            
        if a_weight == "heavy" and t_weight == "light":
             return False, f"{attacker.name}'s momentum overpowers your flow!", {}

        effects.apply_effect(target, "riposte_ready", 2)
        effects.apply_effect(attacker, "staggered", 4)
        return True, "You flow around the strike, readying a counter!", {"power_mult": 0}

    # --- KNIGHT: BULWARK ---
    if "ready_bulwark" in t_effects:
        if "blunt" in attack_tags or "shield_breaker" in attack_tags:
            return False, f"{attacker.name}'s blow shatters through your guard!", {}

        effects.apply_effect(target, "riposte_ready", 2)
        effects.apply_effect(attacker, "off_balance", 4)
        return True, "You catch the strike on your shield, forcing them open!", {"power_mult": 0}

    # --- BARBARIAN: BLOOD COUNTER ---
    if "blood_counter_ready" in t_effects:
        if "stun" in t_effects or "prone" in t_effects:
             return False, "", {}

        effects.remove_effect(target, "blood_counter_ready")
        return True, "You take the blow and strike back with fury!", {"power_mult": 0.5, "counter_strike": True}

    # --- MAGE: PHASE SHIFT ---
    if "phase_shifted" in t_effects:
        if "arcane" in attack_tags or "void" in attack_tags or "magic" in attack_tags:
             return False, "The arcane nature of the strike anchors you to reality!", {}
        
        return True, "You phase through the physical strike!", {"power_mult": 0}

    # --- WARLOCK: ELDRITCH WARD ---
    if "eldritch_ward_ready" in t_effects:
        resources.modify_resource(target, "concentration", 15, source="Void Ward")
        effects.remove_effect(target, "eldritch_ward_ready")
        return True, "The void swallows the strike and feeds your mind!", {"power_mult": 0}

    # --- ASSASSIN: SMOKE SCREEN ---
    if "smoke_screen" in t_effects:
        if "detection" in attack_tags or "true_sight" in attack_tags:
            return False, "The attacker sees right through the smoke!", {}
            
        effects.apply_effect(target, "concealed", 3)
        return True, "You vanish into the smoke as the strike passes through thin air!", {"power_mult": 0}

    # --- CLERIC: DIVINE GRACE ---
    if "divine_grace_ready" in t_effects:
        resources.modify_resource(target, "concentration", 20, source="Divine Grace")
        effects.remove_effect(target, "divine_grace_ready")
        return True, "A shimmer of divine light intercepts the blow!", {"power_mult": 0}

    # --- BEASTMASTER: BESTIAL REFLEX ---
    if "bestial_bond_active" in t_effects:
        effects.remove_effect(target, "bestial_bond_active")
        return True, "Your pet leaps in front of the strike, guarding you!", {"power_mult": 0}

    # --- ILLUSIONIST: MIRROR IMAGE ---
    if "mirror_image_active" in t_effects:
        effects.apply_effect(attacker, "confused", 4)
        effects.remove_effect(target, "mirror_image_active")
        return True, "Your image shatters into light, leaving the attacker dazed!", {"power_mult": 0}

    # --- DEFILER: BLOOD VEIL ---
    if "blood_veil_active" in t_effects:
        effects.apply_effect(attacker, "malediction", 6)
        effects.remove_effect(target, "blood_veil_active")
        return True, "Blood mist absorbs the strike, weaving a curse around the attacker!", {"power_mult": 0.5}

    # --- RED MAGE: FENCER'S WARD ---
    if "fencers_ward_active" in t_effects:
        effects.apply_effect(target, "dualcast", 5)
        effects.remove_effect(target, "fencers_ward_active")
        return True, "You parry the strike with fluid grace, charging your next spell!", {"power_mult": 0}

    return False, "", {}
