import json
import os
import sys
import time
import math
import random
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk
from collections import deque

# --- Godless Shard Imports ---
from architect_data import SYM_MAP, PREVIEW_TXT, load_config
import architect_logic as core

# --- Path Injection ---
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from utilities.colors import Colors

class AethelgardArchitect:
    def __init__(self, width=250, height=250, offset_x=0, offset_y=0, zone_prefix=""):
        self.config = load_config()
        size = self.config.get("grid_size", [width, height])
        self.width, self.height = size[0], size[1]
        self.offset_x = offset_x
        self.offset_y = offset_y
        self.zone_prefix = zone_prefix
        self.grid = [["ocean" for _ in range(self.width)] for _ in range(self.height)]
        self.current_phase = 0
        
    def generate_txt_preview(self):
        """Saves a plain text version for record keeping."""
        output = [
            f"=== AETHELGARD TOPOLOGICAL PREVIEW (Phase {self.current_phase}) ===",
            "-" * self.width
        ]
        for y in range(self.height):
            line = "".join(SYM_MAP.get(self.grid[y][x], ".") for x in range(self.width))
            output.append(line)
        output.append("-" * self.width)
        
        os.makedirs(os.path.dirname(PREVIEW_TXT), exist_ok=True)
        with open(PREVIEW_TXT, "w", encoding="utf-8") as f:
            f.write("\n".join(output))

    def run_phase_0(self):
        return core.run_phase_0_logic(self.grid, self.width, self.height, self.config)

    def run_phase_1(self):
        return core.run_phase_1_logic(self.grid, self.width, self.height, self.config)

    def run_phase_2(self):
        return core.run_phase_2_logic(self.grid, self.width, self.height)

    def run_phase_3(self):
        print("\n--- Running Phase 3: POI Placement & Road Pathfinding ---")
        hubs = self.config.get("kingdoms", {})
        hub_coords = {}
        for k_id, data in hubs.items():
            cx, cy = int(data["center"][0]), int(data["center"][1])
            hub_coords[k_id] = (cx, cy)
            # Cities are now hubs of cobblestone and dirt
            for dy in range(-6, 7):
                for dx in range(-6, 7):
                    dist_sq = dx*dx + dy*dy
                    if dist_sq < 16:
                        if 0 <= cx+dx < self.width and 0 <= cy+dy < self.height:
                            self.grid[cy+dy][cx+dx] = "city"
                    elif dist_sq < 36:
                        if 0 <= cx+dx < self.width and 0 <= cy+dy < self.height:
                            if self.grid[cy+dy][cx+dx] not in ["water", "ocean"]:
                                self.grid[cy+dy][cx+dx] = "cobblestone"

        target = (self.width // 2, self.height // 2)
        self.grid[target[1]][target[0]] = "city" # Crossroads
        for k_id, start_coord in hub_coords.items():
            path = core.run_road_pathfinding(self.grid, self.width, self.height, start_coord, target)
            if path:
                for idx, (px, py) in enumerate(path):
                    if self.grid[py][px] not in ["city", "water"]:
                        # Winding paths transition from cobblestone near cities to dirt roads
                        if idx < 15 or len(path) - idx < 15:
                            self.grid[py][px] = "cobblestone"
                        else:
                            self.grid[py][px] = "road"
        return True

    def run_phase_4(self):
        """Bridge detection and path refinement."""
        for y in range(self.height):
            for x in range(self.width):
                if self.grid[y][x] in ["road", "cobblestone"]:
                    is_bridge = False
                    for dy, dx in [(0,1), (0,-1), (1,0), (-1,0)]:
                        if 0 <= x+dx < self.width and 0 <= y+dy < self.height:
                            if self.grid[y+dy][x+dx] in ["water", "ocean"]:
                                is_bridge = True
                                break
                    if is_bridge:
                        self.grid[y][x] = "bridge"
        return True

    def run_phase_5(self):
        return core.run_phase_5_logic(self.grid, self.width, self.height, self.config)

    def run_phase_6(self):
        """Phase 6: Sharded Export (The Godless Standard)."""
        print("\n--- Running Phase 6: Sharded Export ---")
        from utilities.mapper import TERRAIN_ELEVS

        # Define Region Boundaries for Sharding
        half_w, half_h = self.width // 2, self.height // 2
        
        zone_definitions = {
            f"{self.zone_prefix}aetheria": {"x_range": [0, half_w], "y_range": [0, half_h], "name": f"{self.zone_prefix.title()}Kingdom of Aetheria"},
            f"{self.zone_prefix}umbra": {"x_range": [half_w, self.width], "y_range": [0, half_h], "name": f"{self.zone_prefix.title()}Shadow Lands of Umbra"},
            f"{self.zone_prefix}sylvanis": {"x_range": [0, half_w], "y_range": [half_h, self.height], "name": f"{self.zone_prefix.title()}Sylvanis Wilds"},
            f"{self.zone_prefix}null_void": {"x_range": [half_w, self.width], "y_range": [half_h, self.height], "name": f"{self.zone_prefix.title()}The Null Wastes"}
        }

        shards = {z_id: {"metadata": {"id": z_id, "name": data["name"], "grid_logic": True, "security_level": "wilderness", "target_cr": 10}, "rooms": []} 
                  for z_id, data in zone_definitions.items()}

        # Metadata Constants for V7.2
        TERRAIN_DATA = {
            "mountain": {"opacity": 0.8, "cost": 10},
            "high_mountain": {"opacity": 1.0, "cost": 25},
            "peak": {"opacity": 1.0, "cost": 50},
            "forest": {"opacity": 0.3, "cost": 3},
            "dense_forest": {"opacity": 0.6, "cost": 5},
            "water": {"opacity": 0.1, "cost": 10},
            "ocean": {"opacity": 0.1, "cost": 20},
            "city": {"opacity": 0.0, "cost": 1},
            "road": {"opacity": 0.0, "cost": 1},
            "cobblestone": {"opacity": 0.0, "cost": 1},
            "swamp": {"opacity": 0.4, "cost": 6},
            "plains": {"opacity": 0.0, "cost": 2},
            "grass": {"opacity": 0.1, "cost": 2},
            "hills": {"opacity": 0.4, "cost": 4},
            "beach": {"opacity": 0.0, "cost": 2},
            "wasteland": {"opacity": 0.2, "cost": 3}
        }

        for y in range(self.height):
            for x in range(self.width):
                cell = self.grid[y][x]
                
                # Apply Offsets
                real_x = x + self.offset_x
                real_y = y + self.offset_y
                
                # Find Zone
                zone_id = "null_void"
                for z_id, bounds in zone_definitions.items():
                    if bounds["x_range"][0] <= x < bounds["x_range"][1] and \
                       bounds["y_range"][0] <= y < bounds["y_range"][1]:
                        zone_id = z_id
                        break
                
                # Elevation logic (introducing variance for natural look)
                base_z = TERRAIN_ELEVS.get(cell, 0)
                variance = 0
                if cell == "mountain":
                    variance = random.randint(-1, 2)
                elif cell == "high_mountain":
                    variance = random.randint(-1, 3)
                elif cell == "hills":
                    variance = random.randint(-1, 1)
                elif cell == "peak":
                    variance = random.randint(0, 5)
                
                elevation = base_z + variance
                
                # Grid Logic: V7.2 Coordinate Standards
                room_id = f"{zone_id}.{real_x}.{real_y}.0"
                
                # Generate Exits (Standard 4-way Grid)
                exits = {
                    "north": f"{zone_id}.{real_x}.{real_y - 1}.0",
                    "south": f"{zone_id}.{real_x}.{real_y + 1}.0",
                    "east": f"{zone_id}.{real_x + 1}.{real_y}.0",
                    "west": f"{zone_id}.{real_x - 1}.{real_y}.0"
                }

                # Boundary Check for Exits (Optional: remove if borders should loop or be 'void')
                if y == 0: exits.pop("north")
                if y == self.height - 1: exits.pop("south")
                if x == 0: exits.pop("west")
                if x == self.width - 1: exits.pop("east")

                # Deterministic POI Naming
                center = self.width // 2
                if x == center and y == center:
                    room_name = "The Great Aethelgard Crossroads"
                else:
                    room_name = f"{cell.replace('_', ' ').title()}"

                # Symbol variety for natural mapping (V7.2 Standard)
                # Use {Colors.X} tokens instead of direct injection to prevent ANSI corruption in JSON.
                symbol_palettes = {
                    "forest": ["{Colors.GREEN}^{Colors.RESET}", "{Colors.GREEN}f{Colors.RESET}", "{Colors.GREEN}t{Colors.RESET}"],
                    "dense_forest": ["{Colors.BOLD}{Colors.GREEN}^{Colors.RESET}", "{Colors.BOLD}{Colors.GREEN}T{Colors.RESET}"],
                    "mountain": ["{Colors.WHITE}^{Colors.RESET}"], 
                    "high_mountain": ["{Colors.BOLD}{Colors.WHITE}^{Colors.RESET}"],
                    "peak": ["{Colors.BOLD}{Colors.WHITE}A{Colors.RESET}"],
                    "plains": ["{Colors.GREEN}.{Colors.RESET}", "{Colors.GREEN},{Colors.RESET}", "{Colors.GREEN}·{Colors.RESET}"],
                    "grass": ["{Colors.GREEN}\"{Colors.RESET}", "{Colors.GREEN}'{Colors.RESET}"],
                    "city": ["{Colors.BOLD}{Colors.YELLOW}#{Colors.RESET}", "{Colors.BOLD}{Colors.YELLOW}H{Colors.RESET}"]
                }
                
                room_symbol = None
                if cell in symbol_palettes:
                    room_symbol = random.choice(symbol_palettes[cell])

                t_data = TERRAIN_DATA.get(cell, {"opacity": 0.0, "cost": 2})

                room_data = {
                    "id": room_id,
                    "zone_id": zone_id,
                    "name": room_name,
                    "description": f"A vast expanse of {cell.replace('_', ' ')} within {zone_id.title()} [V7.2 Verified].",
                    "terrain": str(cell),
                    "symbol": room_symbol,
                    "x": int(real_x), "y": int(real_y), "z": 0,
                    "elevation": int(elevation),
                    "opacity": t_data["opacity"],
                    "traversal_cost": t_data["cost"],
                    "exits": exits,
                    "manual_exits": False,
                    "items": [],
                    "monsters": [],
                    "doors": {}
                }
                
                # SPECIAL: A tree in Sylvanis
                if x == 58 and y == 109 and zone_id == "sylvanis":
                     room_data["items"].append({
                         "name": "ancient gnarled oak",
                         "description": "An ancient oak tree with thick, twisting branches.",
                         "type": "object"
                     })
                     
                shards[zone_id]["rooms"].append(room_data)

        # Write Shards
        for z_id, data in shards.items():
            path = f"data/zones/{z_id}.json"
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
                
        print(f"Exported {len(shards)} sharded zone files.")
        return True

    def run_gui(self):
        root = tk.Tk()
        root.title("Aethelgard Architect: Premium Edition")
        root.geometry("1400x900")
        root.configure(bg="#0a0a0a")
        
        TAG_COLORS = {
            "ocean": "#000080", "plains": "#2e7d32", "mountain": "#757575",
            "high_mountain": "#bdbdbd", "peak": "#eeeeee", "water": "#0288d1",
            "city": "#ffd600", "bridge": "#ff6f00", "desert": "#ffecb3",
            "forest": "#1b5e20", "dense_forest": "#003300", "grass": "#4caf50",
            "road": "#5d4037", "cobblestone": "#455a64", "dirt_road": "#8d6e63",
            "beach": "#fff9c4", "hills": "#9e9d24", "swamp": "#4e342e",
            "wasteland": "#37474f"
        }

        # Simplified GUI for this demo
        main_frame = tk.Frame(root, bg="#0a0a0a")
        main_frame.pack(fill=tk.BOTH, expand=True)
        sidebar = tk.Frame(main_frame, bg="#111", width=250)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        text_area = scrolledtext.ScrolledText(main_frame, bg="#000", fg="#eee", font=("Courier", 7), wrap=tk.NONE)
        text_area.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        for name, color in TAG_COLORS.items():
            text_area.tag_configure(name, foreground=color)

        def update_display():
            text_area.delete('1.0', tk.END)
            for y in range(self.height):
                line_data = []
                for x in range(self.width):
                    cell = self.grid[y][x]
                    sym = SYM_MAP.get(cell, ".")
                    text_area.insert(tk.END, sym, cell)
                text_area.insert(tk.END, "\n")

        def on_next_phase():
            phases = [self.run_phase_0, self.run_phase_1, self.run_phase_2, 
                      self.run_phase_3, self.run_phase_4, self.run_phase_5, self.run_phase_6]
            if self.current_phase < len(phases):
                if phases[self.current_phase]():
                    self.current_phase += 1
                    update_display()
                else: messagebox.showerror("Error", "Phase failed")

        tk.Button(sidebar, text="NEXT PHASE", command=on_next_phase, bg="#222", fg="#fff", pady=10).pack(fill=tk.X, padx=10, pady=10)
        tk.Button(sidebar, text="AUTO-GEN", command=lambda: [on_next_phase() for _ in range(7-self.current_phase)], bg="#333", fg="#fff").pack(fill=tk.X, padx=10, pady=10)
        
        update_display()
        root.mainloop()

if __name__ == "__main__":
    architect = AethelgardArchitect()
    architect.run_gui()
