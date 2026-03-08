"""
logic/modules/common/combat.py
Universal Combat Handlers for Players.
"""
import logging
from logic import calibration

logger = logging.getLogger("GodlessMUD")

def stop_combat(player):
    """Clears combat state for the player and their target."""
    if player.fighting:
        target = player.fighting
        player.fighting = None
        # Reciprocal stop
        if hasattr(target, 'stop_combat'):
            target.stop_combat()
        elif hasattr(target, 'fighting') and target.fighting == player:
            target.fighting = None
            
    player.attackers = []
    if player.state == "combat":
        player.state = "normal"

def get_total_defense(player):
    """Calculates total defense from Armor, Shields, Kit, and Buffs."""
    total_def = 0
    
    # 1. Armor & Shield
    if player.equipped_armor:
        total_def += getattr(player.equipped_armor, 'defense', 0)
    if player.equipped_offhand:
        total_def += getattr(player.equipped_offhand, 'defense', 0)
        
    # 2. Kit Bonus
    kit_mult = player.active_kit.get('defense_multiplier', 1.0)
    total_def = int(total_def * kit_mult)
    
    # 3. Buffs/Effects
    for effect_id in player.status_effects:
        effect_data = player.game.world.status_effects.get(effect_id)
        if effect_data:
            mods = effect_data.get('modifiers', {})
            total_def += mods.get('defense_add', 0)
            
    return min(calibration.MaxValues.DEFENSE, int(total_def))
