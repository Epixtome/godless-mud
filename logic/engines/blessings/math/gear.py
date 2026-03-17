"""
logic/engines/blessings/math/gear.py
The Gear Grammar: Standardized tagging and material interactions.
Pillar: Identity Tags on Gear drive deterministic math payoffs.
"""
import logging
from logic import calibration

logger = logging.getLogger("GodlessMUD")

def get_gear_tags(entity):
    """
    Harvests all tags from equipped items.
    Priority: 1. equipped_armor, 2. equipped_weapon, 3. accessory slots.
    """
    all_tags = []
    slots = ["equipped_armor", "equipped_head", "equipped_neck", "equipped_arms", 
             "equipped_hands", "equipped_legs", "equipped_feet", "equipped_offhand", "equipped_weapon"]
    
    for slot in slots:
        item = getattr(entity, slot, None)
        if item:
            item_tags = getattr(item, 'tags', [])
            if isinstance(item_tags, list):
                all_tags.extend(item_tags)
            elif isinstance(item_tags, str):
                all_tags.append(item_tags)
                
    return all_tags

def calculate_gear_damage_mult(target, attack_tags):
    """
    Evaluates how the target's gear materials interact with the attack's identity.
    V6.0: Material Grammar (Conductivity, Flammability).
    """
    mult = 1.0
    gear_tags = get_gear_tags(target)
    
    # 1. Conductivity (Metal + Lightning)
    if "lightning" in attack_tags and "material_metal" in gear_tags:
        mult *= calibration.MaterialGrammar.METAL_LIGHTNING_MULT
        
    # 2. Flammability (Wood/Cloth + Fire)
    if "fire" in attack_tags:
        if "material_wood" in gear_tags:
            mult *= calibration.MaterialGrammar.WOOD_FIRE_MULT
        if "material_cloth" in gear_tags:
            mult *= calibration.MaterialGrammar.CLOTH_FIRE_MULT
            
    # 3. Void Instability (Void + Holy)
    if "holy" in attack_tags and "material_void" in gear_tags:
        mult *= calibration.MaterialGrammar.VOID_MATERIAL_HOLY_WEAKNESS
        
    # 4. Insulation (Wood/Rubber + Lightning - Resist)
    if "lightning" in attack_tags and "material_wood" in gear_tags:
        mult *= (1.0 - calibration.MaterialGrammar.WOOD_LIGHTNING_RESIST)

    return mult

def calculate_gear_power_bonus(blessing, player, target, base_power):
    """
    Evaluates how the attacker's gear enhances the skill's identity.
    (e.g., 'serrated' gear increases 'bleed' power).
    """
    bonus = 0
    gear_tags = get_gear_tags(player)
    identity = getattr(blessing, 'identity_tags', [])
    
    # Serrated / Bleed Synergy
    if "bleed" in identity and "serrated" in gear_tags:
        bonus += int(base_power * 0.15)
        
    # Mana Conducting / Arcane Synergy
    if "arcane" in identity and "material_cloth" in gear_tags:
        bonus += int(base_power * calibration.MaterialGrammar.CLOTH_ARCANE_RESONANCE)
        
    # Void Resonance
    if ("void" in identity or "arcane" in identity) and "material_void" in gear_tags:
        bonus += int(base_power * (calibration.MaterialGrammar.VOID_MATERIAL_ARCANE_MULT - 1.0))
        
    # Weighted / Heavy Impact
    if ("blunt" in identity or "physical" in identity) and "weighted" in gear_tags:
        bonus += int(base_power * 0.10)

    return bonus
