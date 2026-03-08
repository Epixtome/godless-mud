from models import Player, Monster
from logic.constants import Tags

def resolve_attack_tags(attacker, blessing=None):
    """
    Synthesizes a master set of tags for a combat action.
    """
    attack_tags = set()
    
    # 1. Base Tags (Weapon/Body)
    if isinstance(attacker, Player):
        if hasattr(attacker, 'equipped_weapon') and attacker.equipped_weapon:
            w_tags = getattr(attacker.equipped_weapon, 'tags', [])
            if isinstance(w_tags, dict):
                attack_tags.update(w_tags.keys())
            elif isinstance(w_tags, list):
                attack_tags.update(w_tags)
        else:
            # Unarmed defaults
            attack_tags.add(Tags.MARTIAL)
            attack_tags.add(Tags.BLUNT)
            
        # Guarantee fallback
        if not attack_tags:
            attack_tags.add(Tags.MARTIAL)
            attack_tags.add(Tags.BLUNT)
            
    elif isinstance(attacker, Monster):
        attack_tags.update(getattr(attacker, 'tags', []))

    # 2. Blessing Overlay
    if blessing:
        b_tags = getattr(blessing, 'identity_tags', [])
        attack_tags.update(b_tags)
        
    return attack_tags
