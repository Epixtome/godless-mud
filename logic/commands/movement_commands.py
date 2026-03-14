"""
logic/commands/movement_commands.py
Core Movement Engine: Cardinal directions, Physics, and Room transitions.
"""
import math
import logic.handlers.command_manager as command_manager
from logic.common import get_reverse_direction
from utilities.colors import Colors
from logic.core import event_engine, resources, effects
from logic.engines import spatial_engine, movement_engine, action_manager
from utilities.mapper import TERRAIN_MAP
from logic.commands.admin.construction.dig_logic import dig_room

def _move(player, direction):
    """Helper function for movement logic."""
    player.refresh_tokens()

    # 0. Status Check
    blocked, reason = effects.is_action_blocked(player, "move")
    if blocked:
        player.send_line(f"{Colors.RED}{reason}{Colors.RESET}")
        return False

    # 1. Spacing Cap
    if player.move_tokens < 0.99:
        player.send_line("You are moving too fast! Wait for your tokens to refresh.")
        return False

    # EVENT: Before Move
    before_ctx = {'player': player, 'direction': direction, 'can_move': True, 'reason': ''}
    event_engine.dispatch("before_move", before_ctx)
    if not before_ctx['can_move']:
        player.send_line(before_ctx['reason'])
        return False

    room = player.room
    if direction not in room.exits:
        if getattr(player, 'autodig', False):
            palette = getattr(player, 'autodig_palette', None)
            copy_target = player.room if palette == 'copy' else None
            terrain = palette if palette in TERRAIN_MAP else None
            new_room = dig_room(player, direction, copy_from=copy_target, terrain=terrain)
            player.send_line(f"Auto-dug {direction} to {new_room.name}.")
        else:
            player.send_line("You cannot go that way.")
            return False

    # Door Check
    door = room.doors.get(direction)
    if door and door.state != 'open':
        player.send_line(f"The {door.name} is {door.state}.")
        return False

    # EVENT: On Exit
    exit_ctx = {'player': player, 'room': room, 'can_exit': True, 'reason': ''}
    event_engine.dispatch("on_exit_room", exit_ctx)
    if not exit_ctx['can_exit']: return False

    target_id = room.exits[direction]
    target_room = player.game.world.rooms.get(target_id)
    if not target_room:
        player.send_line("That exit leads to the void.")
        return False

    # Physics Constraints
    if not getattr(player, 'godmode', False):
        if room.terrain == 'bridge' and target_room.terrain in ['water', 'ocean', 'lake_deep']:
            player.send_line("A sturdy railing prevents you from falling.")
            return False
            
        climb_diff = target_room.elevation - room.elevation
        if climb_diff > 2:
            player.send_line("Too steep to scale.")
            return False
        if climb_diff < -3:
            player.send_line("A sheer drop prevents you from jumping.")
            return False

    # Resource Calculation
    base_cost = movement_engine.calculate_move_cost(player, room)
    elev_diff = target_room.elevation - room.elevation
    elev_penalty = (elev_diff * 20) if elev_diff > 0 else (abs(elev_diff) * 5)
    
    friction = max(1.0, (5.0 - player.move_tokens) * 1.5)
    final_cost = int(math.ceil((base_cost + elev_penalty) * friction))

    if not getattr(player, 'godmode', False):
        if player.resources.get("stamina", 0) < final_cost:
            player.send_line(f"{Colors.RED}Too exhausted to move!{Colors.RESET}")
            return False
            
        resources.modify_resource(player, "stamina", -final_cost, source="Movement", context=direction)
        player.move_tokens = max(0.0, player.move_tokens - 1.0)
        
        if player.resources.get("stamina", 0) < 0:
            effects.apply_effect(player, "exhausted", movement_engine.EXHAUSTION_DURATION)
            player.send_line(f"{Colors.RED}Exhaustion sets in!{Colors.RESET}")
        elif player.resources.get("stamina", 0) < (player.get_max_resource("stamina") * 0.10):
             if not effects.has_effect(player, "panting"):
                 effects.apply_effect(player, "panting", 6)

    # Terrain Delay
    if room.terrain == "swamp" and not getattr(player, 'godmode', False):
        player.send_line("The swamp sucks at your feet...")
        action_manager.start_action(player, 0.5, lambda: _finalize_move(player, direction, target_room, room), tag="moving")
        return True # Note: Technically 'true' as the action is successfully queued, but flee might clear combat too soon.

    return _finalize_move(player, direction, target_room, room)

def _finalize_move(player, direction, target_room, old_room):
    from logic.commands.info.exploration import look
    
    if "concealed" in getattr(player, 'status_effects', {}) and "sneaking" not in getattr(player, 'status_effects', {}):
        effects.remove_effect(player, "concealed")
        player.send_line(f"{Colors.YELLOW}You break stealth by moving!{Colors.RESET}")

    if player in old_room.players: old_room.players.remove(player)
    old_room.broadcast(f"{player.name} leaves {direction}.", exclude_player=player)
    
    player.room = target_room
    target_room.players.append(player)
    target_room.broadcast(f"{player.name} arrives.", exclude_player=player)
    
    # Auto-Paste
    if getattr(player, 'autopaste', False) and (bs := getattr(player, 'brush_settings', None)):
        from logic.commands.admin.construction import utils as construction_utils
        construction_utils.update_room(target_room, zone_id=bs.get('zone'), terrain=bs.get('terrain'), name=bs.get('name'), desc=bs.get('desc'))
        player.send_line(f"Auto-pasted brush.")
    
    # Fog of War
    player.mark_room_visited(target_room.id)
    
    event_engine.dispatch("on_enter_room", {'player': player, 'room': target_room})
    if player.room != target_room: return True # Trap/Teleport check
    
    event_engine.dispatch("after_move", {'player': player, 'old_room': old_room, 'new_room': target_room, 'direction': direction})
    look(player, "", with_prompt=True)
    return True

@command_manager.register("north", "n", category="movement")
def move_north(player, _): return _move(player, "north")
@command_manager.register("south", "s", category="movement")
def move_south(player, _): return _move(player, "south")
@command_manager.register("east", "e", category="movement")
def move_east(player, _): return _move(player, "east")
@command_manager.register("west", "w", category="movement")
def move_west(player, _): return _move(player, "west")
@command_manager.register("up", "u", category="movement")
def move_up(player, _): return _move(player, "up")
@command_manager.register("down", "d", category="movement")
def move_down(player, _): return _move(player, "down")

@command_manager.register("recall", category="movement")
def recall(player, args):
    """Teleport back to the world's starting room."""
    if player.fighting:
        player.send_line("You cannot recall while in combat!")
        return 
    
    start_room = player.game.world.start_room
    if not start_room:
        player.send_line("The word of recall fails to find its tether.")
        return

    player.send_line(f"{Colors.CYAN}A swirling vortex of blue energy consumes you!{Colors.RESET}")
    player.room.broadcast(f"{player.name} vanishes in a flash of azure light!", exclude_player=player)
    
    _finalize_move(player, "the aether", start_room, player.room)
