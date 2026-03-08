import asyncio
import math
import logic.handlers.command_manager as command_manager
from logic.common import get_reverse_direction
from models import Room
from logic import search
from utilities.colors import Colors
from logic.engines import spatial_engine
from logic.core.world import get_room_id
from utilities.mapper import TERRAIN_MAP
import logic.commands.admin.construction.utils as construction_utils
from logic.core import event_engine
from logic.core import resource_engine
from logic.core import status_effects_engine
from logic.engines import movement_engine
from logic.engines import action_manager

def dig_room(player, direction, name="New Room", copy_from=None, terrain=None):
    """Digs a new room in the specified direction."""
    # Calculate new coordinates
    x, y, z = player.room.x, player.room.y, player.room.z
    if direction == 'north': y -= 1
    elif direction == 'south': y += 1
    elif direction == 'east': x += 1
    elif direction == 'west': x -= 1
    elif direction == 'up': z += 1
    elif direction == 'down': z -= 1
    
    # Auto-adjust Z based on target terrain (e.g. Mountain = Z5)
    target_terrain = terrain
    if not target_terrain and copy_from:
        target_terrain = copy_from.terrain
    z = construction_utils.get_terrain_z(target_terrain, z)
    
    # Generate ID
    new_id = get_room_id(player.room.zone_id, x, y, z)
    
    # Check for spatial collision (same zone only)
    existing_room = None
    cross_zone_room = None
    
    # Use spatial engine to find rooms with Z-tolerance (handling slopes)
    spatial = spatial_engine.get_instance(player.game.world)
    candidates = []
    
    # Determine Z-scan range
    # Scan +/- 5 Z-levels to find existing rooms (slopes/hills)
    scan_range = range(z - 5, z + 6)

    for check_z in scan_range:
        r = spatial.get_room(x, y, check_z)
        if r and r != player.room:
            candidates.append(r)
            
    # Sort by proximity to target Z
    candidates.sort(key=lambda r: abs(r.z - z))
    
    for r in candidates:    
        if r.zone_id == player.room.zone_id:
            existing_room = r
            break
        elif not cross_zone_room:
            cross_zone_room = r
            
    if existing_room:
        player.send_line(f"Merged with existing room: {existing_room.name} ({existing_room.id})")
        new_room = existing_room
    elif cross_zone_room:
        player.send_line(f"Auto-linking to existing room in zone '{cross_zone_room.zone_id}': {cross_zone_room.name} ({cross_zone_room.id})")
        new_room = cross_zone_room
    else:
        # Final Safety Check: Ensure we aren't creating a duplicate at exact coords
        # (This handles cases where spatial index might be slightly stale or fuzzy logic missed)
        exact_match = spatial.get_room(x, y, z)
        if exact_match:
             new_room = exact_match
        else:
            # Create Room
            new_room = Room(new_id, name, "An empty room created by magic.")
            new_room.x, new_room.y, new_room.z = x, y, z
            new_room.zone_id = player.room.zone_id
            
            if copy_from:
                new_room.name = copy_from.name
                new_room.description = copy_from.description
                new_room.zone_id = copy_from.zone_id
                new_room.terrain = copy_from.terrain
                
            if terrain:
                new_room.terrain = terrain
            
            # Add to world
            player.game.world.rooms[new_id] = new_room
            
            # Update Spatial Index so the map sees the new room immediately
            spatial_engine.invalidate()
            
            player.send_line(f"Created room '{name}' in zone '{new_room.zone_id}' at {x},{y},{z}.")
    
    # Link Exits
    player.room.add_exit(direction, new_room)
    rev_dir = get_reverse_direction(direction)
    if rev_dir:
        new_room.add_exit(rev_dir, player.room)
    
    return new_room

def _move(player, direction):
    """Helper function for movement logic."""
    # --- KINETIC PACING ENGINE ---
    # 1. Atomic Refill
    player.refresh_tokens()

    # 0. Status Check (Prone/Stalled)
    blocked, reason = status_effects_engine.is_action_blocked(player, "move")
    if blocked:
        player.send_line(f"{Colors.RED}{reason}{Colors.RESET}")
        return True

    # 2. The Hard Wall (5 moves/sec cap)
    # Reject silently if out of tokens (spam protection)
    if player.move_tokens < 0.99:
        return True

    # EVENT: Before Move (Check for combat, resting, etc.)
    before_ctx = {'player': player, 'direction': direction, 'can_move': True, 'reason': ''}
    event_engine.dispatch("before_move", before_ctx)
    if not before_ctx['can_move']:
        player.send_line(before_ctx['reason'])
        return True

    room = player.room
    if direction not in room.exits:
        if getattr(player, 'autodig', False):
            # Auto-Dig
            palette_mode = getattr(player, 'autodig_palette', None)
            copy_target = None
            target_terrain = None
            
            if palette_mode:
                if palette_mode.lower() == 'copy':
                    copy_target = player.room
                elif palette_mode.lower() in TERRAIN_MAP:
                    target_terrain = palette_mode.lower()
            
            new_room = dig_room(player, direction, copy_from=copy_target, terrain=target_terrain)
            
            player.send_line(f"Auto-dug {direction} to {new_room.name} (Terrain: {new_room.terrain}).")
        else:
            player.send_line("You cannot go that way.")
            return True

    # Check door
    door = room.doors.get(direction)
    if door and door.state != 'open':
        player.send_line(f"The {door.name} is {door.state}.")
        return True

    # EVENT: On Exit Room (Hazards, etc.)
    exit_ctx = {'player': player, 'room': room, 'can_exit': True, 'reason': ''}
    event_engine.dispatch("on_exit_room", exit_ctx)
    if not exit_ctx['can_exit']:
        # Reason is sent by the event handler (e.g. death message)
        return True

    target_id = room.exits[direction]
    target_room = player.game.world.rooms.get(target_id)

    if not target_room:
        player.send_line("That exit leads to the void (Room not found).")
        return True

    # --- PHYSICAL CONSTRAINTS ---
    if not getattr(player, 'godmode', False):
        # 1. Bridge Safety
        if room.terrain == 'bridge' and target_room.terrain in ['water', 'ocean', 'lake_deep']:
            player.send_line("A sturdy railing prevents you from accidentally falling into the deep waters.")
            return True
            
        # 2. Elevation Limit (Steep Cliffs)
        climb_diff = target_room.elevation - room.elevation
        if climb_diff > 2:
            player.send_line("The mountain side here is far too steep to scale. You'll need to find a path around.")
            return True
        if climb_diff < -3:
            player.send_line("It's a sheer drop from here. You'd likely break your legs if you tried to jump down.")
            return True

    # --- MVP PHYSICS ENGINE ---
    # Step 3: Calculate Friction + Elevation Penalty
    base_cost = movement_engine.calculate_move_cost(player, room)
    
    # Elevation Penalty: Climbing up is significantly harder
    elev_diff = target_room.elevation - room.elevation
    elev_penalty = 0
    if elev_diff > 0:
        # Climbing: 20 stm per level
        elev_penalty = elev_diff * 20
    elif elev_diff < 0:
        # Descending: 5 stm per level (friction/braking)
        elev_penalty = abs(elev_diff) * 5
    
    tokens = player.move_tokens
    friction = max(1.0, (5.0 - tokens) * 1.5)
    final_cost = int(math.ceil((base_cost + elev_penalty) * friction))

    if not getattr(player, 'godmode', False):
        current_stamina = player.resources.get("stamina", 0)
        
        # Check Affordability
        if current_stamina < final_cost:
            player.send_line(f"{Colors.RED}You are too exhausted to move!{Colors.RESET}")
            # No stall penalty here, just rejection
            return True
            
        # Deduct Resource
        resource_engine.modify_resource(player, "stamina", -final_cost, source="Movement", context=direction)
        
        # Step 4: Execute (Deduct Token)
        player.move_tokens = max(0.0, tokens - 1.0)
        
        # Check Exhaustion (Overdraw Penalty)
        if player.resources.get("stamina", 0) < 0:
            status_effects_engine.apply_effect(player, "exhausted", movement_engine.EXHAUSTION_DURATION)
            player.send_line(f"{Colors.RED}You push yourself to exhaustion!{Colors.RESET}")
        
        # Legacy Panting Check (Optional, keeping for flavor if not exhausted)
        elif (current_stamina - final_cost) < (player.get_max_resource("stamina") * 0.10):
             if not status_effects_engine.has_effect(player, "panting"):
                 status_effects_engine.apply_effect(player, "panting", 6)

    # Swamp Delay (Terrain Interaction)
    if room.terrain == "swamp" and not getattr(player, 'godmode', False):
        player.send_line("The swamp sucks at your feet...")
        
        def _finish_swamp_move():
            _finalize_move(player, direction, target_room, room)
            
        action_manager.start_action(player, 0.5, _finish_swamp_move, tag="moving", fail_msg="Your movement is interrupted!")
        return True

    return _finalize_move(player, direction, target_room, room)

def _finalize_move(player, direction, target_room, old_room):
    """Executes the actual room transition."""
    from logic.commands.info.exploration import look
    
    # Stealth Check
    if "concealed" in getattr(player, 'status_effects', {}):
        if "sneaking" not in getattr(player, 'status_effects', {}):
            from logic.core.engines import status_effects_engine
            status_effects_engine.remove_effect(player, "concealed")
            player.send_line(f"{Colors.YELLOW}You break stealth by moving!{Colors.RESET}")

    # --- Execute Move ---    
    if player in old_room.players:
        old_room.players.remove(player)
    old_room.broadcast(f"{player.name} leaves {direction}.", exclude_player=player)
    
    player.room = target_room
    target_room.players.append(player)
    target_room.broadcast(f"{player.name} arrives.", exclude_player=player)
    
    # Auto-Paste
    if getattr(player, 'autopaste', False) and hasattr(player, 'brush_settings') and player.brush_settings:
        bs = player.brush_settings
        r = target_room
        
        updated = construction_utils.update_room(
            r,
            zone_id=bs.get('zone'),
            terrain=bs.get('terrain'),
            name=bs.get('name'),
            desc=bs.get('desc')
        )
        if updated:
            player.send_line(f"Auto-pasted brush to {r.name}.")
    
    # Update Visited Rooms (Fog of War) - Cap at 200
    if not hasattr(player, 'visited_rooms'):
        player.visited_rooms = []
    elif isinstance(player.visited_rooms, set):
        player.visited_rooms = list(player.visited_rooms)
        
    if target_room.id in player.visited_rooms:
        player.visited_rooms.remove(target_room.id) # Move to end (most recent)
    player.visited_rooms.append(target_room.id)
    
    if len(player.visited_rooms) > 200:
        player.visited_rooms = player.visited_rooms[-200:]
    
    # EVENT: On Enter Room (Traps, Hazards, etc.)
    enter_ctx = {'player': player, 'room': target_room}
    event_engine.dispatch("on_enter_room", enter_ctx)

    # Safety: If player died or was teleported by a trap, stop here to prevent double-look
    if player.room != target_room:
        return True

    # EVENT: After Move (Followers, etc.)
    after_ctx = {'player': player, 'old_room': old_room, 'new_room': target_room, 'direction': direction}
    event_engine.dispatch("after_move", after_ctx)
    
    look(player, "", with_prompt=True)
    return True

@command_manager.register("north", "n", category="movement")
def move_north(player, args):
    """Move north."""
    return _move(player, "north")

@command_manager.register("south", "s", category="movement")
def move_south(player, args):
    """Move south."""
    return _move(player, "south")

@command_manager.register("east", "e", category="movement")
def move_east(player, args):
    """Move east."""
    return _move(player, "east")

@command_manager.register("west", "w", category="movement")
def move_west(player, args):
    """Move west."""
    return _move(player, "west")

@command_manager.register("up", "u", category="movement")
def move_up(player, args):
    """Move up."""
    return _move(player, "up")

@command_manager.register("down", "d", category="movement")
def move_down(player, args):
    """Move down."""
    return _move(player, "down")

@command_manager.register("recall", category="movement")
def recall(player, args):
    """Teleport to the starting room."""
    from logic.commands.info.exploration import look
    if player.is_in_combat():
        player.send_line("You cannot recall while fighting!")
        return
    
    # Determine Kingdom Recall Point from Landmarks
    kingdom = player.identity_tags[0] if player.identity_tags else "neutral"
    target_id = getattr(player.game.world, 'landmarks', {}).get(f"{kingdom}_cap")
    
    target_room = None
    if target_id and target_id in player.game.world.rooms:
        target_room = player.game.world.rooms[target_id]
    
    # Fallback to 0,0,0 (Center of World)
    if not target_room:
        from logic.engines import spatial_engine
        target_room = spatial_engine.get_instance(player.game.world).get_room(0, 0, 0)

    # Fallback to global start room
    if not target_room:
        target_room = player.game.world.start_room or list(player.game.world.rooms.values())[0]

    if not target_room:
        player.send_line("You have nowhere to recall to.")
        return
        
    if player in player.room.players:
        player.room.players.remove(player)
    player.room.broadcast(f"{player.name} disappears in a flash of light.", exclude_player=player)
    
    player.room = target_room
    player.room.players.append(player)
    player.room.broadcast(f"{player.name} appears in a flash of light.", exclude_player=player)
    
    if not hasattr(player, 'visited_rooms'):
        player.visited_rooms = []
    elif isinstance(player.visited_rooms, set):
        player.visited_rooms = list(player.visited_rooms)
        
    if target_room.id in player.visited_rooms:
        player.visited_rooms.remove(target_room.id)
    player.visited_rooms.append(target_room.id)
    look(player, "")

@command_manager.register("mount", category="movement")
def mount(player, args):
    """Mount up, preparing for mounted combat."""
    if not args:
        player.send_line("Mount what?")
        return

    if player.is_mounted:
        player.send_line("You are already mounted.")
        return

    target = search.find_living(player.room, args)
    if not target:
        # Check items too? Usually mounts are mobs.
        player.send_line("You don't see that here.")
        return

    if "mount" not in getattr(target, 'tags', []):
        player.send_line(f"You cannot mount {target.name}.")
        return

    player.is_mounted = True
    player.mount = target
    player.send_line(f"You swing onto {target.name}.")
    player.room.broadcast(f"{player.name} mounts {target.name}.", exclude_player=player)

@command_manager.register("dismount", category="movement")
def dismount(player, args):
    """Dismount."""
    if not player.is_mounted:
        player.send_line("You are not mounted.")
    else:
        player.is_mounted = False
        player.mount = None
        player.send_line("You dismount.")
        player.room.broadcast(f"{player.name} dismounts.", exclude_player=player)

@command_manager.register("enter", category="movement")
def enter_portal(player, args):
    """
    Enter a portal or nexus.
    Usage: enter <portal name>
    """
    if not args:
        player.send_line("Enter what?")
        return
        
    from logic.common import find_by_index
    target = find_by_index(player.room.items, args)
    if not target:
        player.send_line("You don't see that here.")
        return
        
    if "portal" not in getattr(target, 'flags', []):
        player.send_line("You cannot enter that.")
        return
        
    # Nexus Kingdom Check
    if "nexus" in target.flags:
        p_kingdom = player.identity_tags[0] if player.identity_tags else "neutral"
        portal_kingdom = target.metadata.get("kingdom", "neutral")
        
        if p_kingdom != portal_kingdom:
            player.send_line(f"The Nexus rejects you! It is bound to the {portal_kingdom.title()} Kingdom.")
            return
            
    dest_id = target.metadata.get("destination")
    if not dest_id:
        player.send_line("The portal leads nowhere.")
        return
        
    target_room = player.game.world.rooms.get(dest_id)
    if not target_room:
        player.send_line("The destination has crumbled into the void.")
        return
        
    player.send_line(f"You step into the {target.name}...")
    _move_player_instant(player, target_room, "portal")

def _move_player_instant(player, target_room, method="teleport"):
    """Helper for instant movement (teleport/portal)."""
    from logic.commands.info.exploration import look
    
    if player.room:
        if player in player.room.players:
            player.room.players.remove(player)
        player.room.broadcast(f"{player.name} vanishes via {method}.", exclude_player=player)
        
    player.room = target_room
    target_room.players.append(player)
    target_room.broadcast(f"{player.name} arrives via {method}.", exclude_player=player)
    
    look(player, "")

@command_manager.register("stand", category="movement")
def stand(player, args):
    """Stand up from a prone position."""
    if not status_effects_engine.has_effect(player, "prone"):
        player.send_line("You are already standing.")
        return

    stamina_cost = 10
    if player.resources.get("stamina", 0) < stamina_cost:
        player.send_line(f"{Colors.RED}You are too exhausted to stand!{Colors.RESET}")
        return

    # Calculate Delay (Doubled if Stalled/Panting)
    delay = 1.0
    if status_effects_engine.has_effect(player, "stalled") or status_effects_engine.has_effect(player, "panting"):
        delay = 2.0
        player.send_line("You struggle to your feet...")
    else:
        player.send_line("You begin to stand up...")

    def _finish_stand():
        if player.resources.get("stamina", 0) < stamina_cost:
             player.send_line("You don't have the energy to finish standing!")
             return
        
        if status_effects_engine.remove_effect(player, "prone"):
            resource_engine.modify_resource(player, "stamina", -stamina_cost, source="Action", context="Stand")
            player.send_line("You stand up.")
            player.room.broadcast(f"{player.name} stands up.", exclude_player=player)

    action_manager.start_action(player, delay, _finish_stand, tag="standing", fail_msg="You are knocked back down!")