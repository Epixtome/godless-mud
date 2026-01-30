import logic.command_manager as command_manager
from logic.common import get_reverse_direction
from models import Room
from logic import search
from utilities.colors import Colors
from logic.engines import pathfinding_engine
from logic.engines import spatial_engine

def dig_room(player, direction, name="New Room", copy_from=None):
    """Digs a new room in the specified direction."""
    # Calculate new coordinates
    x, y, z = player.room.x, player.room.y, player.room.z
    if direction == 'north': y -= 1
    elif direction == 'south': y += 1
    elif direction == 'east': x += 1
    elif direction == 'west': x -= 1
    elif direction == 'up': z += 1
    elif direction == 'down': z -= 1
    
    # Generate ID
    new_id = f"{player.room.zone_id}_{x}_{y}_{z}".replace("-", "n")
    
    # Check for spatial collision (same zone only)
    existing_room = None
    cross_zone_room = None
    
    # Use spatial engine to find rooms with Z-tolerance (handling slopes)
    spatial = spatial_engine.get_instance(player.game.world)
    candidates = []
    
    # Scan +/- 5 Z-levels to find existing rooms on slopes (Peak Z=5 to Water Z=0)
    for check_z in range(z - 5, z + 6):
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
        # Create Room
        new_room = Room(new_id, name, "An empty room created by magic.")
        new_room.x, new_room.y, new_room.z = x, y, z
        new_room.zone_id = player.room.zone_id
        
        if copy_from:
            new_room.name = copy_from.name
            new_room.description = copy_from.description
            new_room.zone_id = copy_from.zone_id
            new_room.terrain = copy_from.terrain
        
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
    from logic.actions.information import look
    if player.is_in_combat():
        player.send_line("You cannot move while fighting!")
        return

    if getattr(player, 'is_resting', False):
        player.send_line("You are resting.")
        return

    room = player.room
    if direction not in room.exits:
        if getattr(player, 'autodig', False):
            # Auto-Dig
            new_room = dig_room(player, direction)
            player.send_line(f"Auto-dug {direction} to {new_room.name}.")
        else:
            player.send_line("You cannot go that way.")
            return

    # Check door
    door = room.doors.get(direction)
    if door and door.state != 'open':
        player.send_line(f"The {door.name} is {door.state}.")
        return

    target_room = room.exits[direction]

    # Stamina Check
    cost = pathfinding_engine.get_traversal_cost(target_room)
    if player.resources.get('stamina', 0) < cost:
        player.send_line(f"You are too exhausted to move. (Need {cost} ST)")
        return
    player.resources['stamina'] -= cost

    # Move
    if player in room.players:
        room.players.remove(player)
    room.broadcast(f"{player.name} leaves {direction}.", exclude_player=player)
    
    player.room = target_room
    target_room.players.append(player)
    target_room.broadcast(f"{player.name} arrives.", exclude_player=player)
    player.visited_rooms.add(target_room.id)
    
    look(player, "")
    
    # Handle Minions
    if hasattr(player, 'minions') and player.minions:
        for minion in list(player.minions):
            if minion in room.monsters:
                room.monsters.remove(minion)
                room.broadcast(f"{minion.name} leaves {direction}.", exclude_player=player)
                
                minion.room = target_room # Mobs don't usually track room obj, but good for consistency
                target_room.monsters.append(minion)
                target_room.broadcast(f"{minion.name} arrives.", exclude_player=player)
                player.send_line(f"{minion.name} follows you.")

@command_manager.register("north", "n", category="movement")
def move_north(player, args):
    """Move north."""
    _move(player, "north")

@command_manager.register("south", "s", category="movement")
def move_south(player, args):
    """Move south."""
    _move(player, "south")

@command_manager.register("east", "e", category="movement")
def move_east(player, args):
    """Move east."""
    _move(player, "east")

@command_manager.register("west", "w", category="movement")
def move_west(player, args):
    """Move west."""
    _move(player, "west")

@command_manager.register("up", "u", category="movement")
def move_up(player, args):
    """Move up."""
    _move(player, "up")

@command_manager.register("down", "d", category="movement")
def move_down(player, args):
    """Move down."""
    _move(player, "down")

@command_manager.register("recall", category="movement")
def recall(player, args):
    """Teleport to the starting room."""
    from logic.actions.information import look
    if player.is_in_combat():
        player.send_line("You cannot recall while fighting!")
        return
    
    # Determine Kingdom Recall Point from Landmarks
    kingdom = player.identity_tags[0] if player.identity_tags else "neutral"
    target_id = getattr(player.game.world, 'landmarks', {}).get(f"{kingdom}_cap")
    
    target_room = None
    if target_id and target_id in player.game.world.rooms:
        target_room = player.game.world.rooms[target_id]
    
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
    player.visited_rooms.add(target_room.id)
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
    player.send_line(f"You swing onto {target.name}.")
    player.room.broadcast(f"{player.name} mounts {target.name}.", exclude_player=player)

@command_manager.register("dismount", category="movement")
def dismount(player, args):
    """Dismount."""
    if not player.is_mounted:
        player.send_line("You are not mounted.")
    else:
        player.is_mounted = False
        player.send_line("You dismount.")
        player.room.broadcast(f"{player.name} dismounts.", exclude_player=player)