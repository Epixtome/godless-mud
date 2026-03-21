"""
logic/core/resources/stamina.py
Stamina Regeneration and Scaling Logic.
"""
from logic.core import effects

def calculate_stamina_regen(player):
    """Calculates stamina regeneration per tick."""
    if effects.has_effect(player, "atrophy") or "atrophy" in getattr(player, 'status_effects', {}):
        return 0, player.get_max_resource("stamina")

    max_stamina = player.get_max_resource("stamina")
    
    # Base Regen
    regen = 5
    if not player.is_in_combat():
        regen = 15 # Out-of-combat boost
    
    # [V6.0] Terrain Grammar: Stamina
    room = getattr(player, 'room', None)
    if room:
        terrain = getattr(room, 'terrain', '').lower()
        if terrain in ['swamp', 'water', 'ocean']:
            regen = int(regen * 0.5) # High resistance environments drain energy
        elif terrain == 'forest':
            regen += 2 # Fresh air bonus
    
    # [V5.1] Generic Metadata Hook
    for effect_id in getattr(player, 'status_effects', {}):
        meta = effects.get_effect_metadata(effect_id, getattr(player, 'game', None))
        if isinstance(meta, dict):
            if meta.get('regen_suppressed'):
                return 0, max_stamina
            mult = meta.get('stamina_regen_mult', 1.0)
            if isinstance(mult, (int, float)):
                regen = int(regen * mult)

    # Weight Class Logic (Light/Medium recover faster)
    from logic.core.utils import combat_logic
    wc = combat_logic.get_weight_class(player)
    if wc == "light":
        regen += 8
    elif wc == "medium":
        regen += 4
        
    # Resting & Training Bonus
    if player.is_resting:
        regen += 10
        
    if "meditating" in getattr(player, 'status_effects', {}):
        regen += 20
        
    return regen, max_stamina
