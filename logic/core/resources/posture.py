"""
logic/core/resources/posture.py
Posture (Balance) and Heat Dispersion Logic.
"""
from logic.core import effects
from logic.constants import Tags

def calculate_balance_regen(entity):
    """Calculates balance (posture) regeneration per tick."""
    max_bal = 100
    if hasattr(entity, 'get_max_resource'):
        max_bal = entity.get_max_resource('balance')
        
    # [V5.1] Posture Protocol: No passive balance regen in combat or while being attacked
    in_combat = (hasattr(entity, 'is_in_combat') and entity.is_in_combat())
    being_attacked = (hasattr(entity, 'attackers') and len(entity.attackers) > 0)
    
    regen = 0 if (in_combat or being_attacked) else 10
    
    # [V6.0] Terrain Grammar: Balance
    room = getattr(entity, 'room', None)
    if room:
        terrain = getattr(room, 'terrain', '').lower()
        if terrain in ['mountain', 'snow', 'sand', 'mud']:
            regen = int(regen * 0.5) # Unsteady ground slows balance recovery
        elif terrain == 'water':
            regen = int(regen * 0.2) # Extremely hard to find footing in water

    # [V5.1] Generic Metadata Hook
    for effect_id in getattr(entity, 'status_effects', {}):
        meta = effects.get_effect_metadata(effect_id, getattr(entity, 'game', None))
        if isinstance(meta, dict):
            if meta.get('regen_suppressed'):
                return 0, max_bal
            val = meta.get('balance_regen_bonus', 0)
            if isinstance(val, (int, float)):
                regen += int(val)

    return regen, max_bal

def calculate_heat_decay(player):
    """Calculates heat dissipation per tick."""
    max_heat = player.get_max_resource(Tags.HEAT)
    decay = 2
    
    # [V6.0] Terrain Grammar: Heat
    room = getattr(player, 'room', None)
    if room:
        terrain = getattr(room, 'terrain', '').lower()
        if terrain in ['water', 'snow']:
            decay += 10 # Rapid cooling
        elif terrain == 'ocean':
            decay += 20
            
    is_waiting = player.last_action in ["wait", "none", ""]
    
    if is_waiting or player.is_resting or not player.is_in_combat():
        decay += 8 # Base decay boost when idle

    # Knight Passive: Thermal Mass (20% bonus when stationary)
    kit_name = player.active_kit.get('name', '').lower()
    if kit_name == 'knight' and is_waiting:
        decay = int(decay * 1.2)
        
    return decay, max_heat
