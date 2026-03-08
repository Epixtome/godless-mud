import json
import os
import sys

# Add the project root to path to allow importing utilities
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from utilities.mapper import draw_grid, TERRAIN_MAP
from utilities.colors import Colors

def render_tactical_map(x_center, y_center, z_center=0, radius=10, zone_id="sylvanis"):
    """
    Renders a tactical ASCII map for the AI by reading zone data files.
    """
    # Attempt to load zone data
    zone_file = f"data/zones/{zone_id}.json"
    if not os.path.exists(zone_file):
        return f"Error: Zone file {zone_file} not found."

    with open(zone_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    rooms = data.get("rooms", {})
    
    # Simple Mock of the Room class for the draw_grid function
    class MockRoom:
        def __init__(self, room_data):
            self.id = room_data.get("id")
            self.x = room_data.get("x")
            self.y = room_data.get("y")
            self.z = room_data.get("z", 0)
            self.terrain = room_data.get("terrain", "default")
            self.elevation = room_data.get("elevation", 0)
            self.symbol = room_data.get("symbol") # Support for custom architect symbols
            self.zone_id = zone_id

    # Create a grid lookup for the draw_grid function
    grid = {}
    player_room = None
    rooms_found = 0

    for r_data in rooms:
        rx, ry, rz = r_data.get("x"), r_data.get("y"), r_data.get("z", 0)
        # Check if within radius (Z-flattened or specific Z)
        if z_center is None or rz == z_center:
            if abs(rx - x_center) <= radius and abs(ry - y_center) <= radius:
                mock = MockRoom(r_data)
                # Use a Z-priority: if multiple rooms at (x,y), take the one closest to z_center
                k = (rx - x_center, ry - y_center)
                if k not in grid or abs(rz - (z_center or 0)) < abs(grid[k].z - (z_center or 0)):
                    grid[k] = mock
                
                if rx == x_center and ry == y_center and (z_center is None or rz == z_center):
                    player_room = mock
                rooms_found += 1

    if not rooms_found:
        return f"Warning: No rooms found in {zone_id} at {x_center},{y_center} (Z={z_center}).\nCoordinates in Aethelgard are sharded: Aetheria (0-124), Umbra (125-249 X), Sylvanis (125-249 Y), etc."

    if not player_room:
        # Create a dummy center if no room exists exactly at the center
        player_room = MockRoom({"id": "center", "x": x_center, "y": y_center, "z": z_center or 0})

    # Render
    map_lines = draw_grid(grid, player_room, radius=radius, ignore_fog=True)
    return "\n".join(map_lines)

if __name__ == "__main__":
    # Default to Aethelgard center or provided args
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--x", type=int, default=50)
    parser.add_argument("--y", type=int, default=50)
    parser.add_argument("--z", type=int, default=0)
    parser.add_argument("--radius", type=int, default=10)
    parser.add_argument("--zone", type=str, default="sylvanis")
    
    args = parser.parse_args()
    print(render_tactical_map(args.x, args.y, args.z, args.radius, args.zone))
