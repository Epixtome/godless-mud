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
    
    if resource_name == Tags.HEAT:
        return passives.get('max_heat', 100)
            
    return 100

def reset_resources(player):
    """Fully restores and resets all resources to base state."""
    player.hp = player.max_hp
    if 'concentration' in player.resources:
        player.resources['concentration'] = get_max_resource(player, 'concentration')
    if Tags.HEAT in player.resources:
        player.resources[Tags.HEAT] = 0
    if 'stability' in player.resources:
        player.resources['stability'] = get_max_resource(player, 'stability')
    if 'chi' in player.resources:
        player.resources['chi'] = 0
    if 'stamina' in player.resources:
        player.resources['stamina'] = get_max_resource(player, 'stamina')
    
    player.send_line(f"{Colors.CYAN}Your vitals and resources have been reset.{Colors.RESET}")

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
