import json
import os
import random
import math

ATLAS_FILE = os.path.join("data", "atlas.json")

# --- Configuration ---
# Coordinates are now determined by the Ring System, but we keep IDs for reference
KINGDOMS = {
    "light": {"color": "Y"},
    "shadow": {"color": "M"},
    "instinct": {"color": "G"}
}

def generate_atlas():
    print("Generating World Atlas (Continental Web)...")
    nodes = {}
    edges = []

    # 1. The Central Continent (The Hub & Borderlands)
    nodes["hub"] = {
        "id": "hub", "x": 0, "y": 0, 
        "type": "hub", "biome": "wasteland", "name": "The Shard Crater", "radius": 8
    }
    
    # Borderland Outposts (The exits from the center)
    border_radius = 60
    directions = [
        ("north", 270, "light"), 
        ("southeast", 30, "shadow"), 
        ("southwest", 150, "instinct")
    ]
    
    border_nodes = []
    for name, angle, biome in directions:
        rad = math.radians(angle)
        bx = int(border_radius * math.cos(rad))
        by = int(border_radius * math.sin(rad))
        nid = f"border_{name}"
        nodes[nid] = {
            "id": nid, "x": bx, "y": by,
            "type": "outpost", "biome": "borderland", "name": f"{biome.title()} Border Post", "radius": 6
        }
        border_nodes.append(nid)
        # Connect to Hub
        edges.append({"id": f"road_hub_{nid}", "from": "hub", "to": nid, "type": "road", "biome": "wasteland"})

    # Connect Border Posts to each other (Inner Ring)
    for i in range(len(border_nodes)):
        u = border_nodes[i]
        v = border_nodes[(i + 1) % len(border_nodes)]
        edges.append({"id": f"inner_{u}_{v}", "from": u, "to": v, "type": "road", "biome": "borderland"})

    # 2. The Continents (Clusters of Nodes)
    
    # --- Light Continent (North) ---
    nodes["light_cap"] = {"id": "light_cap", "x": 0, "y": -220, "type": "capital", "biome": "light", "name": "Sanctum", "radius": 18}
    nodes["light_farm"] = {"id": "light_farm", "x": -50, "y": -180, "type": "outpost", "biome": "light", "name": "Golden Fields", "radius": 10}
    nodes["light_mine"] = {"id": "light_mine", "x": 50, "y": -180, "type": "dungeon", "biome": "light", "name": "Crystal Caverns", "radius": 10}
    nodes["light_port"] = {"id": "light_port", "x": 0, "y": -280, "type": "outpost", "biome": "light", "name": "Port Solas", "radius": 8}
    
    edges.append({"id": "bridge_light", "from": "border_north", "to": "light_farm", "type": "road", "biome": "light"}) # Land Bridge
    edges.append({"id": "road_farm_cap", "from": "light_farm", "to": "light_cap", "type": "road", "biome": "light"})
    edges.append({"id": "road_mine_cap", "from": "light_mine", "to": "light_cap", "type": "road", "biome": "light"})
    edges.append({"id": "road_port_cap", "from": "light_port", "to": "light_cap", "type": "road", "biome": "light"})
    edges.append({"id": "road_farm_mine", "from": "light_farm", "to": "light_mine", "type": "road", "biome": "light"})

    # --- Shadow Continent (South East) ---
    nodes["shadow_cap"] = {"id": "shadow_cap", "x": 190, "y": 110, "type": "capital", "biome": "shadow", "name": "Noxus", "radius": 18}
    nodes["shadow_swamp"] = {"id": "shadow_swamp", "x": 140, "y": 80, "type": "dungeon", "biome": "shadow", "name": "Obsidian Marsh", "radius": 12}
    nodes["shadow_ruins"] = {"id": "shadow_ruins", "x": 240, "y": 80, "type": "dungeon", "biome": "shadow", "name": "Ancient Ruins", "radius": 10}
    nodes["shadow_void"] = {"id": "shadow_void", "x": 190, "y": 170, "type": "dungeon", "biome": "shadow", "name": "Void Scar", "radius": 10}

    edges.append({"id": "bridge_shadow", "from": "border_southeast", "to": "shadow_swamp", "type": "road", "biome": "shadow"})
    edges.append({"id": "road_swamp_cap", "from": "shadow_swamp", "to": "shadow_cap", "type": "road", "biome": "shadow"})
    edges.append({"id": "road_ruins_cap", "from": "shadow_ruins", "to": "shadow_cap", "type": "road", "biome": "shadow"})
    edges.append({"id": "road_void_cap", "from": "shadow_void", "to": "shadow_cap", "type": "road", "biome": "shadow"})

    # --- Instinct Continent (South West) ---
    nodes["instinct_cap"] = {"id": "instinct_cap", "x": -190, "y": 110, "type": "capital", "biome": "instinct", "name": "Ironbark", "radius": 18}
    nodes["instinct_jungle"] = {"id": "instinct_jungle", "x": -140, "y": 80, "type": "dungeon", "biome": "instinct", "name": "Verdant Jungle", "radius": 12}
    nodes["instinct_canyon"] = {"id": "instinct_canyon", "x": -240, "y": 80, "type": "dungeon", "biome": "instinct", "name": "Red Canyons", "radius": 10}
    nodes["instinct_tundra"] = {"id": "instinct_tundra", "x": -190, "y": 170, "type": "dungeon", "biome": "instinct", "name": "Frozen Wastes", "radius": 10}

    edges.append({"id": "bridge_instinct", "from": "border_southwest", "to": "instinct_jungle", "type": "road", "biome": "instinct"})
    edges.append({"id": "road_jungle_cap", "from": "instinct_jungle", "to": "instinct_cap", "type": "road", "biome": "instinct"})
    edges.append({"id": "road_canyon_cap", "from": "instinct_canyon", "to": "instinct_cap", "type": "road", "biome": "instinct"})
    edges.append({"id": "road_tundra_cap", "from": "instinct_tundra", "to": "instinct_cap", "type": "road", "biome": "instinct"})

    # 3. The Outer Web (Inter-Continental Connections)
    # Light <-> Shadow (North-East)
    nodes["wild_ashlands"] = {"id": "wild_ashlands", "x": 100, "y": -100, "type": "dungeon", "biome": "wasteland", "name": "The Ashlands", "radius": 8}
    edges.append({"id": "path_light_ash", "from": "light_mine", "to": "wild_ashlands", "type": "road", "biome": "wasteland"})
    edges.append({"id": "path_shadow_ash", "from": "shadow_ruins", "to": "wild_ashlands", "type": "road", "biome": "wasteland"})

    # Shadow <-> Instinct (South)
    nodes["wild_deep"] = {"id": "wild_deep", "x": 0, "y": 180, "type": "dungeon", "biome": "wasteland", "name": "The Deep Wilds", "radius": 8}
    edges.append({"id": "path_shadow_deep", "from": "shadow_void", "to": "wild_deep", "type": "road", "biome": "wasteland"})
    edges.append({"id": "path_instinct_deep", "from": "instinct_tundra", "to": "wild_deep", "type": "road", "biome": "wasteland"})

    # Instinct <-> Light (North-West)
    nodes["wild_peaks"] = {"id": "wild_peaks", "x": -100, "y": -100, "type": "dungeon", "biome": "wasteland", "name": "Storm Peaks", "radius": 8}
    edges.append({"id": "path_instinct_peaks", "from": "instinct_canyon", "to": "wild_peaks", "type": "road", "biome": "wasteland"})
    edges.append({"id": "path_light_peaks", "from": "light_farm", "to": "wild_peaks", "type": "road", "biome": "wasteland"})

    atlas = {"nodes": nodes, "edges": edges}
    
    os.makedirs(os.path.dirname(ATLAS_FILE), exist_ok=True)
    with open(ATLAS_FILE, 'w') as f:
        json.dump(atlas, f, indent=4)
        
    print(f"Atlas generated with {len(nodes)} nodes and {len(edges)} edges.")
    visualize_atlas(atlas)

def visualize_atlas(atlas):
    print("\n--- World Atlas Preview ---")
    width, height = 80, 40
    min_x, max_x = -300, 300
    min_y, max_y = -300, 300
    
    grid = [[' ' for _ in range(width)] for _ in range(height)]
    
    def to_grid(wx, wy):
        nx = (wx - min_x) / (max_x - min_x)
        ny = (wy - min_y) / (max_y - min_y)
        gx = int(nx * (width - 1))
        gy = int((1 - ny) * (height - 1))
        return gx, gy

    # Draw Edges
    for edge in atlas['edges']:
        if edge['from'] not in atlas['nodes'] or edge['to'] not in atlas['nodes']: continue
        n1 = atlas['nodes'][edge['from']]
        n2 = atlas['nodes'][edge['to']]
        x1, y1 = to_grid(n1['x'], n1['y'])
        x2, y2 = to_grid(n2['x'], n2['y'])
        
        # Bresenham line
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy
        while True:
            if 0 <= x1 < width and 0 <= y1 < height:
                if grid[y1][x1] == ' ': grid[y1][x1] = '.'
            if x1 == x2 and y1 == y2: break
            e2 = 2 * err
            if e2 > -dy: err -= dy; x1 += sx
            if e2 < dx: err += dx; y1 += sy

    # Draw Nodes
    for n in atlas['nodes'].values():
        gx, gy = to_grid(n['x'], n['y'])
        if 0 <= gx < width and 0 <= gy < height:
            char = 'O'
            if n['type'] == 'capital': char = '#'
            elif n['type'] == 'dungeon': char = '!'
            grid[gy][gx] = char

    print("-" * width)
    for row in grid:
        print("".join(row))
    print("-" * width)

if __name__ == "__main__":
    generate_atlas()
