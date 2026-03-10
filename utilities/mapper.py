from utilities.colors import Colors

TERRAIN_MAP = {
    "road": f"{Colors.YELLOW}+{Colors.RESET}",
    "dirt_road": f"{Colors.YELLOW}.{Colors.RESET}",
    "plains": f"{Colors.GREEN}.{Colors.RESET}",
    "grass": f"{Colors.GREEN}\"{Colors.RESET}",
    "hills": f"{Colors.GREEN}n{Colors.RESET}",
    "forest": f"{Colors.GREEN}^{Colors.RESET}",
    "dense_forest": f"{Colors.BOLD}{Colors.GREEN}^{Colors.RESET}",
    "mountain": f"{Colors.WHITE}^{Colors.RESET}",
    "high_mountain": f"{Colors.BOLD}{Colors.WHITE}^{Colors.RESET}",
    "peak": f"{Colors.BOLD}{Colors.WHITE}A{Colors.RESET}",
    "swamp": f"{Colors.MAGENTA}%{Colors.RESET}",
    "water": f"{Colors.BLUE}~{Colors.RESET}",
    "shallow_water": f"{Colors.CYAN}~{Colors.RESET}",
    "ocean": f"{Colors.BOLD}{Colors.BLUE}~{Colors.RESET}", # Safer character
    "beach": f"{Colors.YELLOW}.{Colors.RESET}",
    "indoors": f"{Colors.CYAN}#{Colors.RESET}",
    "cave": f"{Colors.WHITE}o{Colors.RESET}",
    "desert": f"{Colors.YELLOW}:{Colors.RESET}",
    "wasteland": f"{Colors.RED}:{Colors.RESET}",
    "bridge": f"{Colors.YELLOW}={Colors.RESET}",
    "cobblestone": f"{Colors.BOLD}{Colors.WHITE}.{Colors.RESET}",
    "city": f"{Colors.BOLD}{Colors.YELLOW}@{Colors.RESET}",
    "neutral": ".",
    "default": "."
}

TERRAIN_HEIGHTS = {
    "mountain": 5,
    "high_mountain": 10,
    "peak": 15,
    "hills": 3,
    "bridge": 1,
    "beach": 0,
    "water": -1,
    "shallow_water": -1,
    "ocean": -5,
    "deep_water": -5,
    "underwater": -10,
    "sky": 50,
    "cloud": 40,
    "abyss": -100
}

TERRAIN_PRIORITY = [
    "shop", "gate", "wall", "bridge", "rail", 
    "road", "dirt_road", "cobblestone",
    "peak", "high_mountain", "mountain", "hills",
    "river", "ocean", "deep_water", "water", "shallow_water", 
    "cave", "dense_forest", "great_tree", "great_forest", "forest", 
    "swamp", "jungle",
    "desert", "wasteland", "ice",
    "plains", "grass", "beach", "indoors"
]

def get_terrain_char(room):
    """Gets the ASCII character for a given room object or terrain name."""
    if isinstance(room, str):
        return TERRAIN_MAP.get(room, TERRAIN_MAP["default"])
        
    # If the room has a custom prescribed symbol (e.g. from the Architect), use it.
    if hasattr(room, 'symbol') and room.symbol:
        return room.symbol
        
    terrain = getattr(room, 'terrain', 'default')
    return TERRAIN_MAP.get(terrain, TERRAIN_MAP["default"])

def get_map_header(room, world=None):
    """Returns a formatted header string with Zone and Coordinates."""
    zone_name = "Unknown Zone"
    if room.zone_id:
        if world and room.zone_id in world.zones:
            zone_name = world.zones[room.zone_id].name
        else:
            zone_name = room.zone_id.replace('_', ' ').title()
        
    return f"{Colors.BOLD}[ {zone_name} ({room.x}, {room.y}, {room.z}) ]{Colors.RESET}"

def draw_grid(grid, player_room, radius=None, visited_rooms=None, ignore_fog=False, indent=0, world=None):
    """
    Draws a map from a pre-computed grid of rooms.
    grid: {(rx, ry): Room}
    player_room: The central room object for the '@' symbol.
    radius: Optional radius. If None, uses elevation-adaptive scaling (Tactical Map).
    visited_rooms: A set of room IDs the player has visited for Fog of War.
    ignore_fog: If True, shows all rooms regardless of visited status.
    indent: Number of spaces to prepend to each line.
    """
    
    # Radius Logic:
    # 1. If radius is provided (like radius=2 for Look), use it.
    # 2. If radius is None (Tactical Map), scale based on elevation.
    if radius is None:
        # Dynamic Radius: High ground sees farther. Base radius is 7 (15x15).
        # Elevation -5 -> Radius 2
        # Elevation 0 -> Radius 7
        # Elevation +5 -> Radius 12
        radius = 7 + getattr(player_room, 'elevation', 0)
        radius = max(2, min(15, radius))
    
    output = []
    prefix = " " * indent
    
    # Header metadata including Elevation
    header = get_map_header(player_room, world)
    elev_text = f" {Colors.CYAN}[Elev: {getattr(player_room, 'elevation', 0)}]{Colors.RESET}"
    output.append(f"{prefix}{header}{elev_text}")

    for y in range(-radius, radius + 1):
        line = ""
        for x in range(-radius, radius + 1):
            char = f"{Colors.BOLD}{Colors.WHITE}.{Colors.RESET}"  # Fog

            if (x, y) in grid:
                room = grid[(x, y)]
                is_visited = visited_rooms is None or room.id in visited_rooms

                if ignore_fog or is_visited:
                    if room == player_room:
                        char = f"{Colors.BOLD}{Colors.RED}@{Colors.RESET}"
                    else:
                        base_char = get_terrain_char(room)
                        
                        # Visual Depth Shading:
                        # Higher rooms from player viewpoint = Bold
                        # Lower/Level = Standard
                        diff = getattr(room, 'elevation', 0) - getattr(player_room, 'elevation', 0)
                        if diff > 0:
                            char = f"{Colors.BOLD}{base_char}{Colors.RESET}"
                        else:
                            char = base_char
            
            line += f"{char} "
        output.append(prefix + line)
    return output