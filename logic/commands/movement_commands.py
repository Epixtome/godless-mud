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
        return True

    # 1. Spacing Cap
    if player.move_tokens < 0.99:
        player.send_line("You are moving too fast! Wait for your tokens to refresh.")
        return True

    # EVENT: Before Move
    before_ctx = {'player': player, 'direction': direction, 'can_move': True, 'reason': ''}
    event_engine.dispatch("before_move", before_ctx)
    if not before_ctx['can_move']:
        player.send_line(before_ctx['reason'])
        return True

    room = player.room
    if direction not in room.exits:
        if getattr(player, 'autodig', False):
            # Check for Architect Stencil first
            copy_target = None
            terrain = None
            
            if hasattr(player, 'builder_state') and player.builder_state["active"]:
                from logic.commands.admin.construction.builder_state import _load_kit
                k_data = _load_kit(player.builder_state["kit"])
                if k_data:
                    idx = player.builder_state["stencil_index"]
                    if 0 < idx <= len(k_data["templates"]):
                        stencil = k_data["templates"][idx-1]
                        terrain = stencil.get('terrain')
            
            # Legacy/Manual override
            if not terrain:
                kit_override = getattr(player, 'autodig_kit', None)
                if kit_override == 'copy': copy_target = player.room
                elif kit_override in TERRAIN_MAP: terrain = kit_override

            new_room = dig_room(player, direction, copy_from=copy_target, terrain=terrain)
            player.send_line(f"{Colors.GREEN}Auto-shaping {direction}...{Colors.RESET}")
        else:
            player.send_line("You cannot go that way.")
            return True

    # Door Check
    door = room.doors.get(direction)
    if door and door.state != 'open':
        player.send_line(f"The {door.name} is {door.state}.")
        return True

    # EVENT: On Exit
    exit_ctx = {'player': player, 'room': room, 'can_exit': True, 'reason': ''}
    event_engine.dispatch("on_exit_room", exit_ctx)
    if not exit_ctx['can_exit']: return True

    target_id = room.exits[direction]
    target_room = player.game.world.rooms.get(target_id)
    if not target_room:
        player.send_line("That exit leads to the void.")
        return True

    # Physics Constraints
    if not getattr(player, 'godmode', False):
        if room.terrain == 'bridge' and target_room.terrain in ['water', 'ocean', 'lake_deep']:
            player.send_line("A sturdy railing prevents you from falling.")
            return True
            
        climb_diff = getattr(target_room, 'elevation', 0) - getattr(room, 'elevation', 0)
        if climb_diff > 2:
            player.send_line("Too steep to scale.")
            return True
        if climb_diff < -3:
            player.send_line("A sheer drop prevents you from jumping.")
            return True

    # Resource Calculation
    base_cost = movement_engine.calculate_move_cost(player, room)
    elev_diff = getattr(target_room, 'elevation', 0) - getattr(room, 'elevation', 0)
    elev_penalty = (elev_diff * 20) if elev_diff > 0 else (abs(elev_diff) * 5)
    
    friction = max(1.0, (5.0 - player.move_tokens) * 1.5)
    final_cost = int(math.ceil((base_cost + elev_penalty) * friction))

    if not getattr(player, 'godmode', False):
        # [V6.0] Terrain Hazards (The Grammar)
        if room.terrain in ['mud', 'snow'] and effects.has_effect(player, "off_balance"):
            effects.apply_effect(player, "prone", 4)
            player.send_line(f"{Colors.RED}You lose your footing on the {room.terrain} and fall!{Colors.RESET}")
            return True # Movement failed due to fall, but don't disconnect

        if room.terrain == 'swamp' and player.resources.get("stamina", 0) < 10:
            effects.apply_effect(player, "immobilized", 6)
            player.send_line(f"{Colors.YELLOW}The thick muck of the swamp entangles your exhausted limbs!{Colors.RESET}")
            return True

        if player.resources.get("stamina", 0) < final_cost:
            player.send_line(f"{Colors.RED}Too exhausted to move!{Colors.RESET}")
            return True
            
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

    from logic.core.services import world_service
    world_service.move_entity(player, target_room)
    
    target_room.broadcast(f"{player.name} arrives.", exclude_player=player)
    
    # Auto-Paste
    if getattr(player, 'autopaste', False) and (bs := getattr(player, 'brush_settings', None)):
        from logic.commands.admin.construction import utils as construction_utils
        construction_utils.update_room(target_room, zone_id=bs.get('zone'), terrain=bs.get('terrain'), name=bs.get('name'), desc=bs.get('desc'))
        player.send_line(f"Auto-pasted brush.")
    
    # Fog of War
    player.mark_room_visited(target_room.id)
    
    if player.room != target_room: return True # Trap/Teleport check
    
    event_engine.dispatch("after_move", {'player': player, 'old_room': old_room, 'new_room': target_room, 'direction': direction})
    look(player, "", with_prompt=True)
    return True

@command_manager.register("climb", category="movement")
def climb(player, args):
    """
    Scale steep terrain that is otherwise impassable.
    Usage: climb <direction>
    Example: climb north
    Rules: 1 tick delay (2s), 4x elevation stamina penalty.
    """
    if not args:
        player.send_line("Climb which direction?")
        return True
    
    direction_input = args.split()[0].lower()
    
    # Map common directional aliases
    dir_map = {
        "n": "north", "s": "south", "e": "east", "w": "west", 
        "u": "up", "d": "down", "ne": "northeast", "nw": "northwest",
        "se": "southeast", "sw": "southwest"
    }
    direction = dir_map.get(direction_input, direction_input)
    
    room = player.room
    if direction not in room.exits:
        player.send_line(f"You cannot climb to the {direction}.")
        return True

    # 1. Status & Token Check
    blocked, reason = effects.is_action_blocked(player, "move")
    if blocked:
        player.send_line(f"{Colors.RED}{reason}{Colors.RESET}")
        return True

    if player.move_tokens < 0.99:
        player.send_line("You are moving too fast! Wait for your tokens to refresh.")
        return True

    target_id = room.exits[direction]
    target_room = player.game.world.rooms.get(target_id)
    if not target_room:
        player.send_line("The cliffside leads into a void of nothingness.")
        return True

    # 2. Physics Check
    elev_diff = getattr(target_room, 'elevation', 0) - getattr(room, 'elevation', 0)
    
    # Define climbing limits: (3-6 for up, -4--6 for down)
    can_climb = False
    msg = ""
    if 0 < elev_diff <= 6:
        can_climb = True
        msg = f"You begin to pull yourself up the steep incline to the {direction}..."
    elif -6 <= elev_diff < 0:
        can_climb = True
        msg = f"You begin to carefully descend the sheer drop to the {direction}..."
    
    if not can_climb:
        if elev_diff > 6:
            player.send_line("That is far too steep for even a skilled climber.")
        elif elev_diff < -6:
            player.send_line("That drop is too sheer to climb without professional gear.")
        else:
            player.send_line("You don't need to 'climb' to go that way. Just walk.")
        return True

    # 3. Resource Calculation
    # We use a base cost but avoid double-penalizing weight if modify_resource handles it.
    # However, calculate_move_cost is the standard for terrain-based exertion.
    base_cost = movement_engine.calculate_move_cost(player, room)
    # Hefty but balanced penalty (24 per elevation units)
    climb_penalty = abs(elev_diff) * 24 
    final_cost = int(math.ceil(base_cost + climb_penalty))

    if player.resources.get("stamina", 0) < final_cost:
        player.send_line(f"{Colors.RED}Too exhausted to attempt the climb!{Colors.RESET}")
        return True

    # 4. Start Delayed Action (1 Tick / 2.0s as requested)
    player.send_line(f"{Colors.CYAN}{msg}{Colors.RESET}")
    player.room.broadcast(f"{player.name} begins to carefully climb toward the {direction}.", exclude_player=player)
    
    def on_complete():
        # Final validation
        if player.room != room: return 
        
        resources.modify_resource(player, "stamina", -final_cost, source="Climbing", context=direction)
        player.move_tokens = max(0.0, player.move_tokens - 1.0)
        
        player.send_line(f"{Colors.GREEN}With a final heave, you pull yourself into the new area.{Colors.RESET}")
        _finalize_move(player, direction, target_room, room)

    action_manager.start_action(player, 2.0, on_complete, tag="climbing", fail_msg="The climb was interrupted!")
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
