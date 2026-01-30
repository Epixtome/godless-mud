import logging
from logic import command_manager
from utilities.colors import Colors
from utilities import combat_formatter

logger = logging.getLogger("GodlessMUD")

def apply_effect(target, effect_id, duration_seconds):
    """Applies a status effect to a target for a duration."""
    game = getattr(target, 'game', None)
    if not game:
        logger.warning(f"Cannot apply effect {effect_id} to {target.name}: No game reference.")
        return

    effect_data = game.world.status_effects.get(effect_id)
    if not effect_data:
        logger.warning(f"Attempted to apply unknown status effect: {effect_id}")
        return

    # 1.5 Handle Exclusivity (Groups)
    # If this effect belongs to a group (e.g., "stance"), remove other effects of that group.
    group = effect_data.get('group')
    if group and hasattr(target, 'status_effects'):
        to_remove = []
        for existing_id in target.status_effects:
            existing_data = game.world.status_effects.get(existing_id)
            if existing_data and existing_data.get('group') == group:
                to_remove.append(existing_id)
        for old_id in to_remove:
            remove_effect(target, old_id)

    expiry_tick = game.tick_count + (duration_seconds // 2) # Assuming 2s tick
    
    if not hasattr(target, 'status_effects'):
        target.status_effects = {}
        
    target.status_effects[effect_id] = expiry_tick
    
    effect_name = effect_data['name']
    if hasattr(target, 'send_line'):
        target.send_line(f"You are now {effect_name}.")

def remove_effect(target, effect_id):
    """Safely removes an effect and notifies the target."""
    if hasattr(target, 'status_effects') and effect_id in target.status_effects:
        del target.status_effects[effect_id]
        
        game = getattr(target, 'game', None)
        if game:
            effect_data = game.world.status_effects.get(effect_id)
            if effect_data and hasattr(target, 'send_line'):
                target.send_line(f"You are no longer {effect_data['name']}.")

def process_effects(game):
    """Called by the heartbeat to manage effect expiry."""
    # Process Players
    for entity in list(game.players.values()):
        _process_entity_effects(game, entity)
        
    # Process Mobs (Iterate rooms to find active mobs)
    for room in game.world.rooms.values():
        for entity in list(room.monsters):
            _process_entity_effects(game, entity)

def _process_entity_effects(game, entity):
    if not hasattr(entity, 'status_effects') or not entity.status_effects:
        return

    expired_effects = []
    for effect_id, expiry_tick in entity.status_effects.items():
        # 1. Handle Expiry
        if game.tick_count >= expiry_tick:
            expired_effects.append(effect_id)
            continue
        
        # 2. Handle DoT (Damage over Time)
        effect_data = game.world.status_effects.get(effect_id)
        if effect_data and 'dot' in effect_data:
            damage = effect_data['dot'].get('damage', 0)
            if damage > 0:
                entity.hp -= damage
                if hasattr(entity, 'send_line'):
                    entity.send_line(f"{Colors.RED}You take {damage} damage from {effect_data['name']}!{Colors.RESET}")
                if entity.room:
                    # Optional: Broadcast to room? Might be too spammy.
                    pass
                
                # Handle Death from DoT
                if entity.hp <= 0:
                    # We rely on the next combat round or a separate check to clean up dead entities
                    # to avoid circular import issues with combat_processor here.
                    pass

    for effect_id in expired_effects:
        del entity.status_effects[effect_id]
        effect_data = game.world.status_effects.get(effect_id)
        if effect_data and hasattr(entity, 'send_line'):
            entity.send_line(f"You are no longer {effect_data['name']}.")

def is_action_blocked(player, command_name):
    """The core gatekeeper check. Returns (True, "Reason") if blocked."""
    if not player.status_effects:
        return False, "OK"

    cmd_category = command_manager.get_command_category(command_name)
    
    for effect_id in player.status_effects:
        effect_data = player.game.world.status_effects.get(effect_id)
        if effect_data and cmd_category in effect_data.get('blocks', []):
            reason = f"You cannot do that while {effect_data['name']}."
            return True, reason
            
    return False, "OK"
