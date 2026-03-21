
from utilities.colors import Colors
import re
import time
from logic.core.utils import vision_logic

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
    "holy": f"{Colors.BOLD}{Colors.YELLOW}*{Colors.RESET}",
    "shadow": f"{Colors.MAGENTA}:{Colors.RESET}",
    "neutral": ".",
    "default": "."
}

# V7.0 Standard: TERRAIN_ELEVS defines surface height on the Z=0 plane.
TERRAIN_ELEVS = {
    "hills": 3, "mountain": 5, "high_mountain": 10, "peak": 15,
    "bridge": 1, "beach": 0, "water": -1, "shallow_water": -1
}

# V7.0 Standard: TERRAIN_PLANES defines structural plane shifts (distinct layers).
TERRAIN_PLANES = {
    "sky": 50, "cloud": 40, "abyss": -100, 
    "ocean": 0, "deep_water": 0, "underwater": -1 # Underwater is the first sub-plane.
}

TERRAIN_PRIORITY = [
    "indoors", "city", "shop", "holy", "gate", "wall", "bridge", "rail", 
    "road", "dirt_road", "cobblestone",
    "peak", "high_mountain", "mountain", "hills",
    "river", "ocean", "deep_water", "water", "shallow_water", 
    "cave", "dense_forest", "great_tree", "great_forest", "forest", 
    "swamp", "jungle",
    "desert", "wasteland", "ice",
    "plains", "grass", "beach"
]

def get_terrain_char(room):
    """Gets the ASCII character for a given room object or terrain name."""
    if isinstance(room, str):
        return TERRAIN_MAP.get(room, TERRAIN_MAP["default"])
    if hasattr(room, 'symbol') and room.symbol:
        return Colors.translate(room.symbol)
    terrain = getattr(room, 'terrain', 'default')
    char = TERRAIN_MAP.get(terrain, TERRAIN_MAP["default"])
    
    # Elevation Overrides (V7.2)
    elev = getattr(room, 'elevation', 0)
    if elev >= 10:
        return f"{Colors.WHITE}#{Colors.RESET}" # Mountain Peak
    elif elev >= 5 and char in ['.', '+']: # If it's flat ground but has high elevation
        return f"{Colors.DGREY}^{Colors.RESET}" # Artificial Hill
        
    return char

def get_map_header(room, world=None):
    """Returns a formatted header string with Zone and Coordinates."""
    zone_name = "Unknown Zone"
    if room.zone_id:
        if world and room.zone_id in world.zones:
            zone_name = world.zones[room.zone_id].name
        else:
            zone_name = room.zone_id.replace('_', ' ').title()
            
    elev = getattr(room, 'elevation', 0)
    return f"{Colors.BOLD}[ {zone_name} ({room.x}, {room.y}, {room.z}) ]{Colors.RESET}{Colors.CYAN} [Elev: {elev}]{Colors.RESET}"

def draw_grid(perception, visited_rooms=None, discovered_rooms=None, ignore_fog=False, indent=0, world=None, shading=True, show_dynamic=True):
    """
    [V6.8 Refactor] Dumb Renderer for PerceptionResults.
    Renders terrain and intelligence strictly from the perception pipeline.
    """
    player_room = perception.observer_room
    radius = perception.radius
    grid = perception.rooms
    entities = perception.entities
    pings = perception.pings
    
    output = []
    prefix = " " * indent
    
    # 1. Header (Static metadata)
    header = get_map_header(player_room, world)
    output.append(f"{prefix}{header}")

    # 2. Grid Traversal
    for y in range(-radius, radius + 1):
        line = ""
        for x in range(-radius, radius + 1):
            char = " "  # Fog/Unknown (V7.0 Polish: Clearer than '.' which conflicts with Plains)

            if (x, y) in grid:
                room = grid[(x, y)]
                is_visited = visited_rooms is None or room.id in visited_rooms
                
                # [V7.2] Persistence Expansion: Checked discovered geography
                is_discovered = (discovered_rooms is not None) and (room.id in discovered_rooms)

                # Fog of War / Knowledge: 
                # radius 3 is always "Visible" while present.
                dist = max(abs(x), abs(y))
                is_knowledge = ignore_fog or dist <= 3 or is_discovered

                if is_visited or is_knowledge:
                    if room == player_room:
                        char = f"{Colors.BOLD}{Colors.RED}@{Colors.RESET}"
                    else:
                        base_char = get_terrain_char(room)
                        has_entity = False
                        
                        # A. Physical Intelligence (Visible Players/Mobs)
                        if (x, y) in entities:
                            for entity in entities[(x, y)]:
                                from models import Player, Monster
                                # Priority: Players (Blue P) > Aggressive (Red M) > Others
                                if isinstance(entity, Player):
                                    base_char = f"{Colors.BLUE}P{Colors.RESET}"
                                    has_entity = True
                                    break
                                else: # Monster
                                    tags = getattr(entity, 'identity_tags', []) + getattr(entity, 'tags', [])
                                    if any(t in tags for t in ["aggressive", "elite", "boss"]):
                                        base_char = f"{Colors.RED}M{Colors.RESET}"
                                        has_entity = True
                                        break
                        
                        # B. Persistent Intelligence (Tracked 'm' or Vibrations '?')
                        if not has_entity:
                            if (x, y) in pings:
                                base_char = f"{Colors.YELLOW}m{Colors.RESET}"
                                has_entity = True
                            
                            # C. Dynamic Events (Vibrations) - Only show if show_dynamic is set
                            elif show_dynamic and dist <= 5:
                                if any(m.fighting for m in room.monsters) or any(p.fighting for p in room.players):
                                    base_char = f"{Colors.MAGENTA}?{Colors.RESET}"
                                    has_entity = True

                        # D. Terrain Rendering (with shading/fog support)
                        if not has_entity:
                            if not is_visited and not ignore_fog:
                                raw_symbol = re.sub(r'\x1b\[[0-9;]*m', '', base_char)
                                base_char = f"{Colors.WHITE}{raw_symbol}{Colors.RESET}"
                                
                            if shading:
                                p_elev = getattr(player_room, 'elevation', 0)
                                r_elev = getattr(room, 'elevation', 0)
                                if r_elev > p_elev:
                                    char = f"{Colors.BOLD}{base_char}{Colors.RESET}"
                                else:
                                    # V7.2 Revision: Keep full colors for lower ground to prevent "Missing Water/Terrain"
                                    char = base_char
                            else:
                                char = base_char
                        else:
                            char = base_char
            
            line += f"{char} "
        output.append(prefix + line)
    return output