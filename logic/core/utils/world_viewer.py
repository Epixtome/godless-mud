
import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

from utilities.colors import Colors

def render_zone_map(world, zone_id):
    """
    Renders an ASCII map of a zone based on room coordinates.
    Returns a string representation.
    """
    rooms = [r for r in world.rooms.values() if r.zone_id == zone_id]
    if not rooms:
        return f"Zone '{zone_id}' not found or has no rooms."

    min_x = min(r.x for r in rooms)
    max_x = max(r.x for r in rooms)
    min_y = min(r.y for r in rooms)
    max_y = max(r.y for r in rooms)

    width = max_x - min_x + 1
    height = max_y - min_y + 1

    # Sanity check for massive zones
    if width > 100 or height > 100:
        return f"Zone '{zone_id}' is too large to render ({width}x{height}). Max 100x100."

    # Grid initialization
    grid = [[" " for _ in range(width)] for _ in range(height)]
    
    # Fill grid
    for r in rooms:
        symbol = "#"
        if r.terrain == "water": symbol = "~"
        elif r.terrain == "mountain": symbol = "^"
        elif r.terrain == "forest": symbol = "f"
        elif r.terrain == "road": symbol = "."
        
        # Invert Y for terminal display (Top-down)
        grid[r.y - min_y][r.x - min_x] = symbol

    # Formatting output
    header = f"--- Map: {zone_id} ({width} x {height}) ---\n"
    legend = "Legend: #=Wall/Room, ~=Water, ^=Mountain, f=Forest, .=Road\n"
    
    map_str = header + legend + "+" + "-" * width + "+\n"
    for row in grid:
        map_str += "|" + "".join(row) + "|\n"
    map_str += "+" + "-" * width + "+"

    return map_str

def find_room_by_fuzzy_name(world, search_term):
    """Finds rooms matching a name for debugging."""
    matches = []
    for r in world.rooms.values():
        if search_term.lower() in r.name.lower():
            matches.append(r)
    return matches
