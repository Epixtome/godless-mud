"""
logic/core/utils/mob_logic.py
Unified logic for Mob entities. Decouples Monster behavior from the data model.
"""
import logging
from utilities.colors import Colors

logger = logging.getLogger("GodlessMUD")

def get_defense(mob):
    """Calculates total defense for a monster."""
    total_def = mob.base_mitigation
    # Add defense from intact body parts
    if hasattr(mob, 'body_parts'):
        for part in mob.body_parts.values():
            if not part.get('destroyed', False):
                total_def += part.get('defense_bonus', 0)
    
    # Add defense from status effects
    if hasattr(mob, 'game') and mob.game:
        for effect_id in mob.status_effects:
            from logic.core.engines import status_effects_engine
            effect_data = status_effects_engine.get_effect_definition(effect_id, mob.game)
            if effect_data:
                mods = effect_data.get('modifiers', {})
                total_def += mods.get('defense_add', 0)
                
    return total_def

def get_damage(mob):
    """Calculates damage including status effects for a monster."""
    total_dmg = mob.damage
    
    if hasattr(mob, 'game') and mob.game:
        for effect_id in mob.status_effects:
            from logic.core.engines import status_effects_engine
            effect_data = status_effects_engine.get_effect_definition(effect_id, mob.game)
            if effect_data:
                mods = effect_data.get('modifiers', {})
                # Multiplicative
                if 'damage_mult' in mods:
                    total_dmg *= mods['damage_mult']
                # Additive
                if 'damage_add' in mods:
                    total_dmg += mods['damage_add']
    return int(total_dmg)

def die(mob):
    """Handles monster death logic."""
    mob.stop_combat()
    # Loot Logic
    if mob.loot_table and mob.game:
        import random
        # Pick one item ID
        item_id = random.choice(mob.loot_table)
        
        # Dynamic Loot Check
        if item_id.startswith("*"):
            from logic.factories import loot_factory
            item = loot_factory.generate_loot(level=mob.level)
        # Static Loot Check
        elif item_id in mob.game.world.items:
            proto = mob.game.world.items[item_id]
            item = proto.clone()
        else:
            item = None

        # Add to room
        if item and mob.room:
            mob.room.add_content(item)
            mob.room.broadcast(f"{mob.name} drops {item.name}.")
