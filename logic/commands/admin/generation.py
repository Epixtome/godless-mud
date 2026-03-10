import logic.handlers.command_manager as command_manager
from models import Room
from logic.core.world import get_room_id
from logic.common import get_reverse_direction
import logic.commands.admin.construction.utils as construction_utils

@command_manager.register("@gen_instinct", admin=True)
def gen_instinct(player, args):
    """
    Generates the Instinct Kingdom layout (20x20) and stitches it.
    Includes Walls, Gates, Roads, and Great Trees.
    """
    start_x, start_y, start_z = player.room.x, player.room.y, player.room.z
    zone_id = "kingdom_instinct"
    
    # Ensure Zone Exists
    if zone_id not in player.game.world.zones:
        from models import Zone
        player.game.world.zones[zone_id] = Zone(zone_id, "The Instinct Kingdom")
        player.send_line(f"Created zone '{zone_id}'.")

    width, height = 20, 20
    created_count = 0
    
    # Define Layout
    # 0 = Forest, 1 = Wall, 2 = Gate, 3 = Road, 4 = Great Tree
    grid = [[0 for _ in range(width)] for _ in range(height)]
    
    # 1. Walls
    for x in range(width):
        grid[0][x] = 1
        grid[height-1][x] = 1
    for y in range(height):
        grid[y][0] = 1
        grid[y][width-1] = 1
        
    # 2. Gates (Midpoints)
    mid_x, mid_y = width // 2, height // 2
    grid[0][mid_x] = 2     # South Gate (y=0)
    grid[height-1][mid_x] = 2 # North Gate (y=19)
    grid[mid_y][0] = 2     # West Gate
    grid[mid_y][width-1] = 2 # East Gate
    
    # 3. Roads (Cross + Ring)
    # Cross
    for x in range(1, width-1):
        grid[mid_y][x] = 3
    for y in range(1, height-1):
        grid[y][mid_x] = 3
        
    # Ring (Inner)
    for x in range(4, width-4):
        grid[4][x] = 3
        grid[height-5][x] = 3
    for y in range(4, height-4):
        grid[y][4] = 3
        grid[y][width-5] = 3
        
    # 4. Great Trees (2x2 blocks in quadrants)
    # Quadrant centers approx: (5,5), (15,5), (5,15), (15,15)
    tree_locs = [(5, 5), (14, 5), (5, 14), (14, 14)]
    for tx, ty in tree_locs:
        for dy in range(2):
            for dx in range(2):
                grid[ty+dy][tx+dx] = 4

    # Generate Rooms
    from logic.engines import spatial_engine
    spatial = spatial_engine.get_instance(player.game.world)

    for y in range(height):
        for x in range(width):
            world_x = start_x + x
            world_y = start_y + y
            
            type_code = grid[y][x]
            terrain = "forest"
            name = "Instinct Forest"
            desc = "Ancient trees loom over the forest floor."
            
            if type_code == 1:
                terrain = "stone_wall"
                name = "Kingdom Wall"
                desc = "A massive wall of moss-covered stone."
            elif type_code == 2:
                terrain = "gate"
                name = "Kingdom Gate"
                desc = "A heavy wooden gate reinforced with iron."
            elif type_code == 3:
                terrain = "dirt_road"
                name = "Forest Path"
                desc = "A worn dirt path winding through the woods."
            elif type_code == 4:
                terrain = "great_tree"
                name = "Great Tree"
                desc = "The base of a colossal tree, large enough to house a building."
            
            # Check for existing room to overwrite
            existing = spatial.get_room(world_x, world_y, start_z)
            if existing:
                existing.zone_id = zone_id
                existing.terrain = terrain
                existing.name = name
                existing.description = desc
            else:
                # Create New Room
                rid = get_room_id(zone_id, world_x, world_y, start_z)
                room = Room(rid, name, desc)
                room.x, room.y, room.z = world_x, world_y, start_z
                room.zone_id = zone_id
                room.terrain = terrain
                player.game.world.rooms[rid] = room
                created_count += 1

    # Rebuild Spatial Index
    spatial_engine.invalidate()
    spatial = spatial_engine.get_instance(player.game.world)
    spatial.rebuild()
    
    # Auto-stitch (Link neighbors)
    links = 0
    directions = {
        "north": (0, -1, 0), "south": (0, 1, 0),
        "east": (1, 0, 0), "west": (-1, 0, 0)
    }
    
    for y in range(height):
        for x in range(width):
            world_x = start_x + x
            world_y = start_y + y
            room = spatial.get_room(world_x, world_y, start_z)
            if not room: continue
            
            for d_name, (dx, dy, dz) in directions.items():
                if d_name in room.exits: continue
                
                neighbor = spatial.get_room(world_x + dx, world_y + dy, start_z + dz)
                if neighbor:
                    room.add_exit(d_name, neighbor)
                    # Reciprocal
                    rev = get_reverse_direction(d_name)
                    if rev and rev not in neighbor.exits:
                        neighbor.add_exit(rev, room)
                    links += 1
    
    player.send_line(f"Generated Instinct Kingdom ({created_count} rooms) and stitched {links} exits at {start_x},{start_y}.")

@command_manager.register("@gen_grid", admin=True)
def gen_grid(player, args):
    """
    Generates a rectangular zone grid.
    Usage: @gen_grid <zone_id> <width> <height> [terrain] [Room Name] [direction]
    Example: @gen_grid swamp_01 20 20 swamp "Murky Bog" east
    """
    if not args:
        player.send_line("Usage: @gen_grid <zone_id> <width> <height> [terrain] [Room Name] [direction]")
        return
        
    parts = args.split()
    if len(parts) < 3:
        player.send_line("Usage: @gen_grid <zone_id> <width> <height> [terrain] [Room Name]")
        return
        
    zone_id = parts[0].lower()
    try:
        width = int(parts[1])
        height = int(parts[2])
    except ValueError:
        player.send_line("Width and Height must be integers.")
        return
        
    # Check for direction in last arg
    direction = None
    if len(parts) > 3:
        possible_dir = parts[-1].lower()
        if possible_dir in ['n', 's', 'e', 'w', 'ne', 'nw', 'se', 'sw', 'north', 'south', 'east', 'west', 'northeast', 'northwest', 'southeast', 'southwest']:
            direction = possible_dir
            parts = parts[:-1]
        
    terrain = parts[3].lower() if len(parts) > 3 else "plains"
    room_name = " ".join(parts[4:]) if len(parts) > 4 else f"{zone_id.replace('_', ' ').title()}"
    
    # Ensure Zone Exists
    if zone_id not in player.game.world.zones:
        from models import Zone
        player.game.world.zones[zone_id] = Zone(zone_id, room_name)
        player.send_line(f"Created new zone entry: '{zone_id}'.")
        
    off_x, off_y = construction_utils.get_directional_offsets(player, width, height, direction)
    if off_x is not None:
        start_x, start_y = off_x, off_y
    else:
        start_x, start_y = player.room.x, player.room.y
        
    start_z = player.room.z
    created_count = 0
    updated_count = 0

    from logic.engines import spatial_engine
    spatial = spatial_engine.get_instance(player.game.world)
    
    for y in range(height):
        for x in range(width):
            world_x = start_x + x
            world_y = start_y + y
            
            existing = spatial.get_room(world_x, world_y, start_z)
            if existing:
                existing.zone_id = zone_id
                existing.terrain = terrain
                existing.name = room_name
                updated_count += 1
            else:
                rid = get_room_id(zone_id, world_x, world_y, start_z)
                room = Room(rid, room_name, "A procedurally generated area.")
                room.x, room.y, room.z = world_x, world_y, start_z
                room.zone_id = zone_id
                room.terrain = terrain
                player.game.world.rooms[rid] = room
                created_count += 1
            
    # Rebuild Spatial & Stitch
    spatial_engine.invalidate()
    spatial_engine.get_instance(player.game.world).rebuild()
    
    # Auto-stitch (Link neighbors)
    links = 0
    directions = {
        "north": (0, -1, 0), "south": (0, 1, 0),
        "east": (1, 0, 0), "west": (-1, 0, 0)
    }
    
    spatial = spatial_engine.get_instance(player.game.world)
    for y in range(height):
        for x in range(width):
            world_x = start_x + x
            world_y = start_y + y
            room = spatial.get_room(world_x, world_y, start_z)
            if not room: continue
            
            for d_name, (dx, dy, dz) in directions.items():
                if d_name in room.exits: continue
                
                neighbor = spatial.get_room(world_x + dx, world_y + dy, start_z + dz)
                if neighbor:
                    room.add_exit(d_name, neighbor)
                    # Reciprocal
                    rev = get_reverse_direction(d_name)
                    if rev and rev not in neighbor.exits:
                        neighbor.add_exit(rev, room)
                    links += 1
                    
    player.send_line(f"Generated {created_count} new rooms, updated {updated_count} rooms for zone '{zone_id}' at {start_x},{start_y},{start_z}.")
    player.send_line(f"Stitched {links} connections.")
