"""
logic/core/utils/player_logic.py
Sharded logic for Player entity to maintain 300-line compliance.
Handles resource calculation and pacing.
"""
import time
from logic import calibration
from logic.constants import Tags
from utilities.colors import Colors

def get_max_hp(player):
    """Calculates Max HP based on kit's passive attributes (V6.0)."""
    base_hp = calibration.MaxValues.HP
    passives = player.active_kit.get('passive_attributes', {})
    bonus = passives.get('max_hp_bonus', 0)
    
    return base_hp + bonus

def get_max_resource(player, resource_name):
    """Calculates max resource values via sharded passive attributes."""
    passives = player.active_kit.get('passive_attributes', {})
    
    # 1. Base Logic
    if resource_name == 'stamina':
        return 100 + passives.get('max_stamina_bonus', 0)

    # 2. Dynamic Attribute Lookup (Agnostic)
    # Checks for 'max_chi', 'max_heat', 'max_entropy', etc.
    attr_key = f"max_{resource_name.lower()}"
    if attr_key in passives:
        return passives.get(attr_key, 100)
    
    # 3. Defaults for common Godless resources
    fallbacks = {
        'chi': 5,
        'momentum': 5,
        'entropy': 5,
        'balance': 100,
        Tags.HEAT: 100
    }
            
    return fallbacks.get(resource_name.lower(), 100)

def reset_resources(player):
    """Fully restores and resets all resources to base state."""
    player.hp = player.max_hp
    
    # 1. Sync resource keys with current kit
    sync_resources(player)
    
    # 2. Refill all current resources
    for res in player.resources:
        if res == Tags.HEAT:
            player.resources[res] = 0
        else:
            player.resources[res] = get_max_resource(player, res)
    
    player.send_line(f"{Colors.CYAN}Your vitals and resources have been reset.{Colors.RESET}")

def sync_resources(player):
    """ Ensures player.resources only contains keys relevant to the current class/kit. """
    standard = ['stamina', 'balance']
    
    # Determine Class-Specific Resources (V6.0 Data-Driven)
    class_res = player.active_kit.get('resources', [])
    if not isinstance(class_res, list): class_res = []
    
    required = standard + class_res
    
    # 1. Add missing required keys
    for res in required:
        if res not in player.resources:
            if res == Tags.HEAT:
                player.resources[res] = 0
            else:
                player.resources[res] = get_max_resource(player, res)
                
    # 2. Prune irrelevant keys
    # Optimization: Use list() to avoid mutation error during iteration
    for res in list(player.resources.keys()):
        if res not in required:
            # Atomic Purge: Also remove from ext_state if not specific to current class
            del player.resources[res]

def refresh_tokens(player):
    """Refills movement tokens based on time elapsed (Kinetic Pacing)."""
    current_time = time.time()
    delta = current_time - player.last_refill_time
    
    REFILL_RATE = 4.0 # Comfortable Walk Speed
    player.move_tokens = min(5.0, player.move_tokens + (delta * REFILL_RATE))
    player.last_refill_time = current_time

def mark_room_visited(player, room_id):
    """
    Business logic for room discovery.
    Updates the player's 200-room MRU list and includes neighbors.
    """
    if not hasattr(player, 'visited_rooms') or player.visited_rooms is None:
        player.visited_rooms = []
    
    if isinstance(player.visited_rooms, set):
        player.visited_rooms = list(player.visited_rooms)
    
    # [V7.2] Persistence Expansion
    # 1. Full Color Visit (Radius 1 / 3x3)
    to_visit = [room_id]
    # 2. Geography Discovery (Radius 3 / 7x7) - NOW LOS AWARE (Task 04 Fix)
    to_discover = [room_id]

    if hasattr(player, 'game') and room_id in player.game.world.rooms:
        from logic.core import perception as vision
        
        # We use a TACTICAL scan to see what can actually be perceived from this vantage point.
        # Discovery should not penetrate solid walls.
        p_result = vision.get_perception(player, radius=3, context=vision.TACTICAL)
        
        for coord, room in p_result.rooms.items():
            # If it's in LOS, we "discover" the terrain
            if coord in p_result.los_mask:
                if room.id not in to_discover:
                    to_discover.append(room.id)
                
                # If it's close (Radius 1), we mark it as "Visited" (Permanent Color Memory)
                dist = max(abs(coord[0]), abs(coord[1]))
                if dist <= 1:
                    if room.id not in to_visit:
                        to_visit.append(room.id)

    # Update Visited (Colored)
    for rid in to_visit:
        if rid in player.visited_rooms: player.visited_rooms.remove(rid)
        player.visited_rooms.append(rid)
    if len(player.visited_rooms) > 200:
        player.visited_rooms = player.visited_rooms[-200:]

    # Update Discovered (Persistent Uncolored)
    if not hasattr(player, 'discovered_rooms'): player.discovered_rooms = []
    for rid in to_discover:
        if rid in player.discovered_rooms: player.discovered_rooms.remove(rid)
        player.discovered_rooms.append(rid)
    if len(player.discovered_rooms) > 1000:
        player.discovered_rooms = player.discovered_rooms[-1000:]

def calculate_total_weight(player, only_equipped=False):
    """Calculates the total weight (LBS) of all equipment and inventory."""
    total = 0
    
    # 1. Equipment
    attrs = [
        "equipped_weapon", "equipped_offhand", "equipped_armor",
        "equipped_head", "equipped_neck", "equipped_shoulders",
        "equipped_arms", "equipped_hands", "equipped_finger_l",
        "equipped_finger_r", "equipped_legs", "equipped_feet",
        "equipped_mount"
    ]
    for attr in attrs:
        item = getattr(player, attr, None)
        if item:
            total += (getattr(item, 'weight', 0) or 0)
            
    # 2. Inventory (Optional)
    if not only_equipped:
        for item in player.inventory:
            total += (getattr(item, 'weight', 0) or 0)
            
    return total

def flush_class_state(player):
    """Removes class-specific stances and passives."""
    from logic.core import effects
    to_remove = []
    if player.status_effects:
        for eff_id in player.status_effects:
            eff_def = effects.get_effect_definition(eff_id, player.game)
            if eff_def and eff_def.get('group') in ['stance', 'class_passive']:
                to_remove.append(eff_id)
    
    for eff in to_remove:
        effects.remove_effect(player, eff)

def load_kit(player, kit_name):
    """Applies a specific class kit via persistence shard."""
    from logic.core.utils import persistence
    success = persistence.load_kit(player, kit_name)
    if success: player.mark_tags_dirty()
    return success

def get_class_bonus(player):
    """Returns the numeric bonus associated with the current kit."""
    return player.active_kit.get('class_bonus', 0)

def get_heat_efficiency(player):
    """Returns the heat cost multiplier for the current kit."""
    return player.active_kit.get('heat_efficiency', 1.0)
