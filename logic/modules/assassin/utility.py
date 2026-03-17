"""
logic/modules/assassin/utility.py
Utility system for Assassin traps and concealed logic.
"""
import random
from logic.core import effects, combat, resources
from utilities.colors import Colors

TRAP_TYPES = {
    "trip": {"name": "Trip Trap", "effect": "prone", "duration": 4, "msg": "A hidden tripwire catches your ankle!"},
    "blind": {"name": "Blind Trap", "effect": "blinded", "duration": 8, "msg": "A pouch of blinding powder explodes in your face!"},
    "web": {"name": "Web Trap", "effect": "immobilized_web", "duration": 10, "msg": "A spray of sticky webbing erupts from a hidden canister!"},
    "sleep": {"name": "Sleeping Trap", "effect": "knockout", "duration": 15, "msg": "A cloud of sweet-smelling gas fills your lungs..."},
    "fire": {"name": "Fire Trap", "damage": "2d8", "msg": "A blast of flame erupts from the ground!"}
}

def set_trap(player, trap_type):
    """Places a trap in the current room."""
    if trap_type not in TRAP_TYPES:
        player.send_line(f"Invalid trap type: {trap_type}")
        return False

    room = player.room
    if 'traps' not in room.metadata:
        room.metadata['traps'] = []

    # [V6.0] Determine owner's kingdom for team recognition
    kingdom = "neutral"
    for k in ["light", "shadow", "dark", "instinct"]:
        if k in player.identity_tags:
            kingdom = k
            break

    trap_data = {
        'type': trap_type,
        'owner': player.name,
        'owner_kingdom': kingdom,
        'room_id': room.id,
        'active': True
    }
    
    room.metadata['traps'].append(trap_data)
    player.send_line(f"{Colors.BLUE}You carefully set a {trap_type} trap in the shadows.{Colors.RESET}")
    return True

def trigger_traps(entity, room):
    """Triggers any active traps in the room for the entity."""
    if 'traps' not in room.metadata or not room.metadata['traps']:
        return

    # Don't trigger your own traps (or your teammates' in the future)
    remaining_traps = []
    triggered = False

    for trap in room.metadata['traps']:
        if not trap['active']: continue
        
        # [V6.0] Trap Safety: Don't trigger your own or your kingdom's traps
        is_owner = trap['owner'] == getattr(entity, 'name', '')
        
        is_teammate = False
        entity_kingdom = "none" # Initialize here to ensure it's always defined
        if hasattr(entity, 'identity_tags') or hasattr(entity, 'tags'):
             entity_tags = getattr(entity, 'identity_tags', []) + getattr(entity, 'tags', [])
             for k in ["light", "shadow", "dark", "instinct"]:
                 if k in entity_tags:
                     entity_kingdom = k
                     break
             is_teammate = trap.get('owner_kingdom') == entity_kingdom and entity_kingdom != "none"
        
        if is_owner or is_teammate:
            remaining_traps.append(trap)
            continue

        # Trigger!
        t_type = trap['type']
        t_def = TRAP_TYPES.get(t_type)
        if not t_def: continue

        triggered = True
        if hasattr(entity, 'send_line'):
            entity.send_line(f"{Colors.RED}{t_def['msg']}{Colors.RESET}")
        
        room.broadcast(f"{entity.name} triggers a hidden trap!", exclude_player=entity)

        if "effect" in t_def:
            effects.apply_effect(entity, t_def['effect'], t_def['duration'])
        
        if "damage" in t_def:
            from utilities.utils import roll_dice
            dmg = roll_dice(t_def['damage'])
            combat.apply_damage(entity, dmg, context=f"{t_type.title()} Trap")

        # Traps are consumed-on-use
        trap['active'] = False

    # Cleanup consumed traps
    room.metadata['traps'] = [t for t in room.metadata['traps'] if t['active']]

def struggle_free(entity):
    """Attempts to break free from immobilization effects."""
    is_immobilized = False
    immobilizing_effects = ["immobilized_web", "net", "tripped", "prone"]
    
    active_cc = [e for e in immobilizing_effects if effects.has_effect(entity, e)]
    if not active_cc:
        entity.send_line("You are not currently restrained.")
        return False

    # Success logic
    success_chance = 0.10 # Base 10%
    
    # Class Bonuses
    if getattr(entity, 'active_class', '') == 'barbarian':
        success_chance = 1.0 # 100%
    elif "martial" in getattr(entity, 'identity_tags', []):
        success_chance += 0.15 # 25% for martial classes

    if random.random() < success_chance:
        entity.send_line(f"{Colors.GREEN}You successfully struggle free!{Colors.RESET}")
        entity.room.broadcast(f"{entity.name} struggles free from their restraints!", exclude_player=entity)
        for e in active_cc:
            effects.remove_effect(entity, e)
        return True
    else:
        entity.send_line("You struggle, but the restraints hold firm.")
        return False
