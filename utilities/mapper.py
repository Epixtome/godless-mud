from utilities.colors import Colors

TERRAIN_MAP = {
    "road": f"{Colors.YELLOW}+{Colors.RESET}",
    "dirt_road": f"{Colors.YELLOW}.{Colors.RESET}",
    "plains": f"{Colors.GREEN}.{Colors.RESET}",
    "hills": f"{Colors.GREEN}n{Colors.RESET}",
    "forest": f"{Colors.GREEN}^{Colors.RESET}",
    "dense_forest": f"{Colors.BOLD}{Colors.GREEN}^{Colors.RESET}",
    "mountain": f"{Colors.WHITE}^{Colors.RESET}",
    "peak": f"{Colors.BOLD}{Colors.WHITE}^{Colors.RESET}",
    "swamp": f"{Colors.MAGENTA}%{Colors.RESET}",
    "water": f"{Colors.BLUE}~{Colors.RESET}",
    "lake_deep": f"{Colors.BLUE}@{Colors.RESET}",
    "deep_water": f"{Colors.BLUE}@{Colors.RESET}",
    "underwater": f"{Colors.BLUE}≈{Colors.RESET}",
    "indoors": f"{Colors.CYAN}#{Colors.RESET}",
    "cave": f"{Colors.WHITE}o{Colors.RESET}",
    "desert": f"{Colors.YELLOW}:{Colors.RESET}",
    "ruins": f"{Colors.WHITE}#",
    "wasteland": f"{Colors.RED}:{Colors.RESET}",
    "ethereal": f"{Colors.MAGENTA}*{Colors.RESET}",
    "ice": f"{Colors.CYAN}.{Colors.RESET}",
    "bridge": f"{Colors.YELLOW}={Colors.RESET}",
    "rail": f"{Colors.BOLD}{Colors.WHITE}#{Colors.RESET}",
    "wall": f"{Colors.BOLD}{Colors.WHITE}#{Colors.RESET}",
    "gate": f"{Colors.BOLD}{Colors.YELLOW}+{Colors.RESET}",
    "shop": f"{Colors.GREEN}${Colors.RESET}",
    "plaza": f"{Colors.BOLD}{Colors.WHITE}O{Colors.RESET}",
    "default": "."
}

def get_terrain_char(terrain):
    """Gets the ASCII character for a given terrain type."""
    return TERRAIN_MAP.get(terrain, TERRAIN_MAP["default"])

def get_map_header(room, world):
    """Returns a formatted header string with Zone and Coordinates."""
    zone_name = "Unknown Zone"
    if room.zone_id and room.zone_id in world.zones:
        zone_name = world.zones[room.zone_id].name
    elif room.zone_id:
        zone_name = room.zone_id.replace('_', ' ').title()
        
    return f"{Colors.BOLD}[ {zone_name} ({room.x}, {room.y}, {room.z}) ]{Colors.RESET}"

def draw_grid(grid, player_room, radius, visited_rooms=None, ignore_fog=False, indent=0):
    """
    Draws a map from a pre-computed grid of rooms.
    grid: {(rx, ry): Room}
    player_room: The central room object for the '@' symbol.
    radius: The display radius (e.g., 7 for a 15x15 map).
    visited_rooms: A set of room IDs the player has visited for Fog of War.
    ignore_fog: If True, shows all rooms regardless of visited status.
    indent: Number of spaces to prepend to each line.
    """
    output = []
    prefix = " " * indent
    for y in range(-radius, radius + 1):
        line = ""
        for x in range(-radius, radius + 1):
            char = f"{Colors.BOLD}{Colors.WHITE}.{Colors.RESET}"  # Fog

            if (x, y) in grid:
                room = grid[(x, y)]
                is_visited = visited_rooms is None or room.id in visited_rooms

                if ignore_fog or is_visited:
                    char = f"{Colors.BOLD}{Colors.RED}@{Colors.RESET}" if room == player_room else get_terrain_char(room.terrain)
            
            line += f" {char} "
        output.append(prefix + line)
    return output