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
    """Calculates Max HP based on kit's passive attributes (V5.9)."""
    base_hp = calibration.MaxValues.HP
    passives = player.active_kit.get('passive_attributes', {})
    bonus = passives.get('max_hp_bonus', 0)
    
    # Legacy support
    if player.active_kit.get('name', '').lower() == 'wanderer':
        bonus = 50
    
    return base_hp + bonus

def get_max_resource(player, resource_name):
    """Calculates max resource values via sharded passive attributes."""
    passives = player.active_kit.get('passive_attributes', {})
    
    if resource_name == 'stamina':
        return 100 + passives.get('max_stamina_bonus', 0)

    if resource_name == 'chi': 
        return passives.get('max_chi', 5)
    
    if resource_name == 'momentum':
        return 5
    
    if resource_name == 'entropy':
        return 5

    if resource_name == Tags.HEAT:
        return passives.get('max_heat', 100)
            
    return 100

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
    
    # 1. Discover target + immediate exits
    to_add = [room_id]
    if hasattr(player, 'game') and room_id in player.game.world.rooms:
        curr = player.game.world.rooms[room_id]
        if hasattr(curr, 'exits'):
            for neighbor_id in curr.exits.values():
                if neighbor_id not in to_add:
                    to_add.append(neighbor_id)

    # 2. Update MRU (Most Recently Used)
    for rid in to_add:
        if rid in player.visited_rooms:
            player.visited_rooms.remove(rid)
        player.visited_rooms.append(rid)
    
    # 3. Enforce 200-room cap (Rule 4.C - Data Optimization)
    if len(player.visited_rooms) > 200:
        player.visited_rooms = player.visited_rooms[-200:]

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
            total += getattr(item, 'weight', 0)
            
    # 2. Inventory (Optional)
    if not only_equipped:
        for item in player.inventory:
            total += getattr(item, 'weight', 0)
        
    return total
