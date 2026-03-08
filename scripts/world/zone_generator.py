import json
import random
import os

class ZoneGenerator:
    """
    Generic procedural zone generator.
    Generates a grid of rooms based on a configuration dictionary.
    """
    def __init__(self, config):
        self.config = config
        self.zone_id = config['id']
        self.zone_name = config['name']
        self.rooms = []
        self.grid = {} # (x,y,z) -> room dict

    def generate(self):
        print(f"Generating {self.zone_name} ({self.zone_id})...")
        
        # 1. Generate Sectors
        for sector in self.config.get('sectors', []):
            self._generate_sector(sector)
            
        # 2. Generate Paths (New: Structured Roads/Rivers)
        for path in self.config.get('paths', []):
            self._generate_path(path)
            
        # 3. Generate Clusters (New: Organic Districts/Islands)
        for cluster in self.config.get('clusters', []):
            self._generate_cluster(cluster)
            
        # 4. Generate Landmarks (overwrites sector rooms if collision)
        for landmark in self.config.get('landmarks', []):
            self._add_room(
                landmark['x'], landmark['y'], landmark.get('z', 0),
                landmark['name'], landmark['description'],
                landmark.get('terrain', 'indoors'),
                is_landmark=True,
                extra_data=landmark
            )
            
        # 5. Connect Grid
        self._connect_grid()
        
        # 6. Export
        self._save_to_file()

    def _generate_sector(self, sector):
        bounds = sector['bounds']
        z = bounds.get('z', 0)
        
        # Determine ranges
        x_min = bounds.get('x_min', 0)
        x_max = bounds.get('x_max', 0)
        y_min = bounds.get('y_min', 0)
        y_max = bounds.get('y_max', 0)

        for x in range(x_min, x_max + 1):
            for y in range(y_min, y_max + 1):
                if random.random() < sector.get('density', 1.0):
                    name = sector.get('room_name', "Wilderness")
                    if isinstance(name, list): name = random.choice(name)
                    
                    desc = sector.get('room_desc', "An area of open terrain.")
                    if isinstance(desc, list): desc = random.choice(desc)
                    
                    self._add_room(x, y, z, name, desc, sector.get('terrain', 'default'))

    def _generate_path(self, path_config):
        """Generates a linear path of rooms between start and end points."""
        start = path_config['start'] # (x, y)
        end = path_config['end']     # (x, y)
        
        x0, y0 = start[0], start[1]
        z = start[2] if len(start) > 2 else 0
        
        x1, y1 = end[0], end[1]
        
        terrain = path_config.get('terrain', 'road')
        name = path_config.get('name', "Path")
        desc = path_config.get('description', "A well-traveled path.")
        style = path_config.get('style', 'straight')
        
        # Bresenham's Line Algorithm for 2D pathing
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        
        while True:
            self._add_room(x0, y0, z, name, desc, terrain)
            if x0 == x1 and y0 == y1: break
            
            # Organic Wobble Logic
            if style == 'organic' and random.random() < 0.3:
                # Pick a random cardinal direction to wobble
                wx, wy = random.choice([(0, 1), (0, -1), (1, 0), (-1, 0)])
                # Only wobble if it doesn't backtrack too hard (simple check)
                self._add_room(x0 + wx, y0 + wy, z, name, desc, terrain)

            e2 = 2 * err
            if e2 > -dy: err -= dy; x0 += sx
            if e2 < dx: err += dx; y0 += sy

    def _generate_cluster(self, cluster):
        """Generates a blob of rooms around a center point."""
        center = cluster['center'] # (x, y, z)
        radius = cluster.get('radius', 3)
        density = cluster.get('density', 0.7)
        
        cx, cy = center[0], center[1]
        cz = center[2] if len(center) > 2 else 0
        
        for x in range(cx - radius, cx + radius + 1):
            for y in range(cy - radius, cy + radius + 1):
                # Euclidean-ish distance check for roundness
                if (x - cx)**2 + (y - cy)**2 <= radius**2:
                    if random.random() < density:
                        name = cluster.get('room_name', "Area")
                        if isinstance(name, list): name = random.choice(name)
                        
                        desc = cluster.get('room_desc', "An area.")
                        if isinstance(desc, list): desc = random.choice(desc)
                        
                        self._add_room(x, y, cz, name, desc, cluster.get('terrain', 'default'))

    def _add_room(self, x, y, z, name, description, terrain, is_landmark=False, extra_data=None):
        # If room exists and we are not a landmark, skip (don't overwrite landmarks with generic)
        if (x, y, z) in self.grid:
            if not is_landmark:
                return self.grid[(x, y, z)]
            # If we are a landmark, we overwrite whatever was there (or update it)
        
        r_id = f"{self.zone_id}_{x}_{y}_{z}".replace("-", "n")
        room = {
            "id": r_id,
            "zone_id": self.zone_id,
            "name": name,
            "description": description,
            "x": x, "y": y, "z": z,
            "terrain": terrain,
            "exits": {}
        }
        
        # Apply extra data (like manual exits or mobs)
        if extra_data:
            if 'monsters' in extra_data: room['monsters'] = extra_data['monsters']
            if 'items' in extra_data: room['items'] = extra_data['items']
            if 'shop_inventory' in extra_data: room['shop_inventory'] = extra_data['shop_inventory']
            if 'manual_exits' in extra_data:
                room['_manual_exits'] = extra_data['manual_exits']

        # Update lists
        if (x, y, z) in self.grid:
            # Overwriting: remove old from list
            old_room = self.grid[(x, y, z)]
            if old_room in self.rooms:
                self.rooms.remove(old_room)
        
        self.rooms.append(room)
        self.grid[(x, y, z)] = room
        return room

    def _connect_grid(self):
        for (x, y, z), room in self.grid.items():
            # Auto-link cardinals
            for dx, dy, direction in [(0, -1, "north"), (0, 1, "south"), 
                                      (1, 0, "east"), (-1, 0, "west")]:
                nx, ny = x + dx, y + dy
                if (nx, ny, z) in self.grid:
                    target = self.grid[(nx, ny, z)]
                    room["exits"][direction] = target["id"]
            
            # Process manual exits
            if '_manual_exits' in room:
                for direction, target_id in room['_manual_exits'].items():
                    # If target_id is relative coords (e.g. "0,0,1"), resolve it
                    if isinstance(target_id, str) and target_id.count(",") == 2:
                        try:
                            tx, ty, tz = map(int, target_id.split(","))
                            tr_id = f"{self.zone_id}_{tx}_{ty}_{tz}".replace("-", "n")
                            room["exits"][direction] = tr_id
                        except ValueError:
                            room["exits"][direction] = target_id
                    else:
                        room["exits"][direction] = target_id
                del room['_manual_exits']

    def _save_to_file(self):
        output_file = os.path.join("data", "zones", f"{self.zone_id}.json")
        data = {
            "zones": [{
                "id": self.zone_id,
                "name": self.zone_name,
                "security_level": self.config.get("security_level", "safe")
            }],
            "rooms": self.rooms
        }
        
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, "w") as f:
            json.dump(data, f, indent=4)
        print(f"Saved {len(self.rooms)} rooms to {output_file}")

if __name__ == "__main__":
    # Example: Generating 'light_mine' (Crystal Caverns)
    config = {
        "id": "light_mine",
        "name": "Crystal Caverns",
        "security_level": "low_sec",
        "sectors": [
            {
                "room_name": ["Crystal Tunnel", "Glimmering Passage"],
                "room_desc": ["The walls glitter with embedded crystals.", "Jagged crystals jut out from the rock."],
                "terrain": "cave",
                "bounds": {"x_min": 0, "x_max": 8, "y_min": 0, "y_max": 8, "z": 0},
                "density": 0.6
            },
            {
                "room_name": "Deep Shaft",
                "room_desc": "A vertical shaft leading deeper into the earth.",
                "terrain": "cave",
                "bounds": {"x_min": 2, "x_max": 6, "y_min": 2, "y_max": 6, "z": -1},
                "density": 0.8
            }
        ],
        "landmarks": [
            {
                "x": 0, "y": 0, "z": 0,
                "name": "Mine Entrance",
                "description": "The entrance to the Crystal Caverns. A cool breeze blows from within.",
                "terrain": "cave"
            },
            {
                "x": 4, "y": 4, "z": -1,
                "name": "The Geode Heart",
                "description": "A massive chamber inside a giant geode. The light is blinding.",
                "terrain": "cave",
                "manual_exits": {"up": "4,4,0"},
                "monsters": ["crystal_golem"]
            },
            {
                "x": 4, "y": 4, "z": 0,
                "name": "Upper Shaft",
                "description": "Looking down, you see a glowing light.",
                "terrain": "cave",
                "manual_exits": {"down": "4,4,-1"}
            }
        ]
    }
    
    generator = ZoneGenerator(config)
    generator.generate()
