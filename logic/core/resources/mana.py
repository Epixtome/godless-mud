"""
logic/core/resources/mana.py
Concentration and Mana Resource Engines.
"""
from logic.constants import Tags

def calculate_conc_regen(player):
    """Calculates concentration regeneration per tick."""
    max_conc = player.get_max_resource(Tags.CONCENTRATION)
    regen = 5
    
    # Tag Bonus
    regen += int(player.get_global_tag_count(Tags.MAGIC) * 0.5)
    
    # [V6.0] Terrain Grammar: Concentration
    room = getattr(player, 'room', None)
    if room:
        terrain = getattr(room, 'terrain', '').lower()
        if terrain == 'void':
            regen = int(regen * 0.5) # Void drains focus
        elif terrain == 'indoors' or terrain == 'library':
             regen += 2 # Quiet environments help focus

    # Modifiers
    if player.is_in_combat():
        # Tension Penalty: Halve regen if hit recently
        if (player.game.tick_count - player.last_hit_tick) <= 2:
            regen = int(regen * 0.5)
    else:
        # Out-of-Combat: Rapid recovery
        regen = 20

    if player.is_resting:
        regen = 30
    if "meditating" in getattr(player, 'status_effects', {}):
        regen += 30
        
    return regen, max_conc
