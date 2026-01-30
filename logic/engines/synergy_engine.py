import logging

logger = logging.getLogger("GodlessMUD")

def calculate_synergies(player):
    """
    Scans player's equipped blessings to determine active Synergies.
    Updates player.active_synergies and player.synergy_bonuses.
    """
    tag_counts = {}
    for b_id in player.equipped_blessings:
        blessing = player.game.world.blessings.get(b_id)
        if not blessing: continue
        for tag in blessing.identity_tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
            
    active_synergies = []
    bonuses = {}
    
    for s_id, synergy in player.game.world.synergies.items():
        match = True
        for req_tag, req_count in synergy.requirements.get('tags', {}).items():
            if tag_counts.get(req_tag, 0) < req_count:
                match = False
                break
        
        if match:
            active_synergies.append(s_id)
            for stat, val in synergy.bonuses.items():
                bonuses[stat] = bonuses.get(stat, 0) + val
                
    player.active_synergies = active_synergies
    player.synergy_bonuses = bonuses