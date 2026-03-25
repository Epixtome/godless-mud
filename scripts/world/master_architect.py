import tkinter as tk
from tkinter import font
import json
import math
import random
import os
import time
import architect_logic as core
from architect_data import SYM_MAP, COLOR_MAP

class AethelgardArchitect:
    def __init__(self):
        self.width = 125
        self.height = 125
        self.grid = [["ocean" for _ in range(self.width)] for _ in range(self.height)]
        
        # [V13.1 SYNC PASS] - Fresh sharding space
        self.offset_x = 9000
        self.offset_y = 9000
        self.offset_z = 0
        self.zone_prefix = "v13_"
        
        # [THE STENCIL OVERLAY - Persistent Layers]
        self.bias_elev = [[0.0 for _ in range(self.width)] for _ in range(self.height)]
        self.bias_moist = [[0.0 for _ in range(self.width)] for _ in range(self.height)]
        self.bias_roads = [[0 for _ in range(self.width)] for _ in range(self.height)] 
        self.bias_biomes = [[None for _ in range(self.width)] for _ in range(self.height)] # Type: list[list[str|None]]
        self.brush_mode = "none" 
        self.brush_radius = 4
        self.show_stencil = None # Initialized in run_gui
        self.biome_categories = {
            "Water": ["ocean", "water", "lake", "swamp"],
            "Land": ["plains", "grass", "meadow", "desert", "wasteland"],
            "Cold": ["snow", "tundra", "glacier"],
            "Peak": ["mountain", "high_mountain", "peak"],
            "Life": ["forest", "dense_forest", "hills"],
            "Meta": ["road", "none"]
        }
        
        # [THE CONTROL DECK - V13Weights]
        self.weights = {
            "seed": "", 
            "sea_level": 0.5, "aridity": 0.5, "mtn_clusters": 0.5, "mtn_scale": 0.5, "peak_intensity": 0.5,
            "volcano_size": 0.5, "ridge_weight": 0.3, "moisture_level": 0.5,
            "inlet_depth": 0.5, "city_hubs": 0.5, "shrine_scatter": 0.5, "road_vines": 0.5, "drift_jaggedness": 0.5
        }
        
        self.cell_size = 6.0
        self.zoom_factor = 1.0
        self.select_start = None
        self.config = self.load_config()
        self.root = None
        self.canvas = None
        self.seed_entry = None
        self.lbl_probe = None

        # Run initial generation
        self.full_generation_pass()

    def load_config(self):
        p = os.path.join(os.path.dirname(__file__), "map_config.json")
        if os.path.exists(p):
            with open(p, "r") as f: return json.load(f)
        return {}

    def save_stencil(self, path="v13_blueprint.stencil"):
        data = {
            "elev": self.bias_elev, 
            "moist": self.bias_moist, 
            "roads": self.bias_roads,
            "biomes": self.bias_biomes
        }
        with open(path, "w") as f: json.dump(data, f)
        self.update_status(f"Stencil saved: {path}")

    def load_stencil(self, path="v13_blueprint.stencil"):
        if os.path.exists(path):
            with open(path, "r") as f:
                data = json.load(f)
                self.bias_elev = data.get("elev", self.bias_elev)
                self.bias_moist = data.get("moist", self.bias_moist)
                self.bias_roads = data.get("roads", self.bias_roads)
                self.bias_biomes = data.get("biomes", self.bias_biomes)
            self.update_status(f"Stencil loaded: {path}")
            self.draw_map()

    def full_generation_pass(self):
        """[V13.1] The Transparent Architect - Synchronized Pipeline."""
        print(f"--- Running v13.1 Architect Pipeline: (Offset {self.offset_x}, {self.offset_y}) ---")
        
        s_val = self.weights.get("seed", "")
        if not s_val: s_val = int(time.time() * 1000) % 1000000
        else:
            try: s_val = int(s_val); 
            except: s_val = hash(str(s_val)) % 1000000
            
        random.seed(s_val); self.config["seed"] = s_val
        self.config.update(self.weights)
        self.config["bias_elev"] = self.bias_elev
        self.config["bias_moist"] = self.bias_moist
        self.config["bias_roads"] = self.bias_roads
        self.config["bias_biomes"] = self.bias_biomes
        
        # Clean shards
        import glob
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        zone_dir = os.path.join(base_dir, "data", "zones")
        stale_shards = glob.glob(os.path.join(zone_dir, f"{self.zone_prefix}*.json"))
        if stale_shards:
            for f in stale_shards:
                try: os.remove(f)
                except: pass
                
        # KINGDOM PLACEMENT
        center_x, center_y = self.width // 2, self.height // 2; radius = self.width // 3.5
        kh_centers = []
        for i in range(3):
            angle = math.radians((i * 120 + random.randint(-15, 15)))
            tx = int(center_x + radius * math.cos(angle)); ty = int(center_y + radius * math.sin(angle)); kh_centers.append([tx, ty])
        k_ids = list(self.config.get("kingdoms", {}).keys())
        for i, k_id in enumerate(k_ids[:3]): self.config["kingdoms"][k_id]["center"] = kh_centers[i]

        # V13.1 FUSION PIPELINE
        grid_meta = core.run_climate_pass(self.grid, self.width, self.height, self.config)
        core.run_phase_0_logic(self.grid, self.width, self.height, self.config) 
        core.run_phase_1_logic(self.grid, self.width, self.height, self.config) 
        core.run_phase_1_5_logic(self.grid, self.width, self.height, self.config) 
        core.run_phase_2_logic(self.grid, self.width, self.height, self.config, grid_meta) 
        core.run_phase_3_logic(self.grid, self.width, self.height, self.config) 
        core.run_phase_4_logic(self.grid, self.width, self.height)              
        core.run_phase_5_logic(self.grid, self.width, self.height, self.config) 
        
        core.run_phase_6_export(
            self.grid, self.width, self.height, self.offset_x, self.offset_y, self.offset_z, 
            self.zone_prefix, self.config
        )
        print(f"--- Generation Complete: V13.1 ---")

    def toggle_stencil(self):
        self.draw_map() 

    def update_status(self, msg):
        if hasattr(self, 'lbl_status') and self.lbl_status: self.lbl_status.config(text=msg.upper())

    def on_canvas_paint(self, event):
        if not self.canvas or self.brush_mode == "none": return
        cx, cy = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        scale = (self.cell_size * self.zoom_factor)
        grid_x, grid_y = int(cx / scale), int(cy / scale)
        R = self.brush_radius
        for dy in range(-R, R+1):
            for dx in range(-R, R+1):
                nx, ny = grid_x + dx, grid_y + dy
                if 0 <= nx < self.width and 0 <= ny < self.height:
                    dist = math.sqrt(dx*dx + dy*dy)
                    if dist < R:
                        # FALLOFF: Smooth blending for climate
                        power = (1.0 - (dist / R)) * 0.4
                        
                        if self.brush_mode == "road": self.bias_roads[ny][nx] = 1 
                        elif self.brush_mode in ["peak", "mountain", "high_mountain"]:
                            self.bias_elev[ny][nx] = min(1.0, self.bias_elev[ny][nx] + power)
                            self.bias_biomes[ny][nx] = self.brush_mode
                        elif self.brush_mode in ["water", "ocean", "lake"]:
                            self.bias_elev[ny][nx] = max(-1.0, self.bias_elev[ny][nx] - power)
                            self.bias_biomes[ny][nx] = self.brush_mode
                        elif self.brush_mode == "desert":
                            self.bias_moist[ny][nx] = max(-1.0, self.bias_moist[ny][nx] - power)
                            self.bias_biomes[ny][nx] = self.brush_mode
                        elif self.brush_mode in ["forest", "dense_forest", "swamp"]:
                            self.bias_moist[ny][nx] = min(1.0, self.bias_moist[ny][nx] + power)
                            self.bias_biomes[ny][nx] = self.brush_mode
                        else:
                            # Direct Biome Suggestion (Heavy Weight)
                            self.bias_biomes[ny][nx] = self.brush_mode
        
        color = "#00bcd4" if self.brush_mode == "road" else "white"
        self.canvas.create_oval(cx-R*scale, cy-R*scale, cx+R*scale, cy+R*scale, outline=color, width=2, tags="brush_preview")
        if self.root: self.root.after(150, lambda: self.canvas.delete("brush_preview") if self.canvas else None)

    def on_canvas_move(self, event):
        if not self.canvas: return
        cx, cy = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        scale = (self.cell_size * self.zoom_factor)
        gx, gy = int(cx / scale), int(cy / scale)
        if 0 <= gx < self.width and 0 <= gy < self.height:
            terr = self.grid[gy][gx]
            abs_x, abs_y = gx + self.offset_x, gy + self.offset_y
            msg = f"COORD: ({abs_x}, {abs_y}) | TERR: {terr.upper()}"
            if hasattr(self, 'lbl_probe') and self.lbl_probe:
                self.lbl_probe.config(text=msg)

    def rerun_generation(self):
        if self.seed_entry: self.weights["seed"] = self.seed_entry.get()
        self.grid = [["ocean" for _ in range(self.width)] for _ in range(self.height)]
        self.full_generation_pass()
        self.draw_map()

    def update_weight(self, key, val): self.weights[key] = float(val)

    def on_zoom(self, event):
        factor = 1.1 if event.delta > 0 else 0.9
        self.zoom_factor *= factor
        if self.zoom_factor < 0.5 or self.zoom_factor > 8.0: self.zoom_factor /= factor; return
        self.canvas.scale("all", 0, 0, factor, factor); self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def draw_map(self):
        if not self.canvas: return
        self.canvas.delete("all")
        self.zoom_factor = 1.0
        scale = self.cell_size
        for y in range(self.height):
            for x in range(self.width):
                terrain = self.grid[y][x]; fill_color = COLOR_MAP.get(terrain, "#000033")
                self.canvas.create_rectangle(x*scale, y*scale, (x+1)*scale, (y+1)*scale, fill=fill_color, outline="", tags="cell")
                
                # STENCIL GHOSTING (V13.1 SAFE CHECK)
                if self.show_stencil and self.show_stencil.get():
                    if self.bias_roads[y][x]:
                        self.canvas.create_rectangle(x*scale+2, y*scale+2, (x+1)*scale-2, (y+1)*scale-2, outline="#00bcd4", width=1, tags="stencil")
                    elif self.bias_biomes[y][x]:
                        # Draw a small indicator of the preferred biome
                        clr = COLOR_MAP.get(self.bias_biomes[y][x], "#fff")
                        self.canvas.create_rectangle(x*scale+2, y*scale+2, (x+1)*scale-2, (y+1)*scale-2, outline=clr, width=1, dash=(2,2), tags="stencil")
                    elif self.bias_elev[y][x] > 0.3:
                        self.canvas.create_line(x*scale, y*scale, (x+1)*scale, (y+1)*scale, fill="#ffffff", width=1, tags="stencil")
                    elif self.bias_moist[y][x] < -0.3: 
                        self.canvas.create_line(x*scale+scale, y*scale, x*scale, y*scale+scale, fill="#ffff00", width=1, tags="stencil")
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def on_canvas_press(self, event):
        if self.brush_mode != "none": self.on_canvas_paint(event)
        else: self.select_start = (self.canvas.canvasx(event.x), self.canvas.canvasy(event.y))

    def on_canvas_drag(self, event):
        if self.brush_mode != "none": self.on_canvas_paint(event)
        elif self.select_start:
            self.canvas.delete("select_box")
            x2, y2 = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
            self.canvas.create_rectangle(self.select_start[0], self.select_start[1], x2, y2, outline="#00bcd4", dash=(4,4), tags="select_box")

    def on_canvas_release(self, event):
        if self.brush_mode != "none": return
        if not self.select_start: return
        
        # Copy to clipboard
        cx, cy = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        scale = (self.cell_size * self.zoom_factor)
        x2, y2 = int(cx / scale), int(cy / scale)
        x1, y1 = int(self.select_start[0] / scale), int(self.select_start[1] / scale)
        
        # Sort coords
        x1, x2 = sorted([x1, x2]); y1, y2 = sorted([y1, y2])
        coord_msg = f"({x1+self.offset_x}, {y1+self.offset_y}) to ({x2+self.offset_x}, {y2+self.offset_y})"
        
        if self.root:
            self.root.clipboard_clear()
            self.root.clipboard_append(coord_msg)
            self.update_status(f"Copied: {coord_msg}")
            
        self.canvas.delete("select_box"); self.select_start = None

    def run_gui(self):
        self.root = tk.Tk()
        self.root.title("Aethelgard Architect: V13.1 SYNC PASS")
        self.root.configure(bg="#111")
        
        # [V13.1] LATE INITIALIZATION OF UI VARS
        self.show_stencil = tk.BooleanVar(value=True)
        
        toolbar = tk.Frame(self.root, bg="#222"); toolbar.pack(side="top", fill="x")
        tk.Button(toolbar, text="REGENERATE", command=self.rerun_generation, bg="#00bcd4", fg="white", font=("Arial", 10, "bold"), padx=10).pack(side="left", padx=5, pady=5)
        tk.Label(toolbar, text="Seed:", bg="#222", fg="#aaa", font=("Arial", 9)).pack(side="left", padx=5)
        self.seed_entry = tk.Entry(toolbar, bg="#333", fg="#fff", width=8); self.seed_entry.pack(side="left", padx=5)
        
        tk.Button(toolbar, text="S-SAVE", command=self.save_stencil, bg="#4caf50", fg="white", font=("Arial", 7)).pack(side="left", padx=2)
        tk.Button(toolbar, text="S-LOAD", command=self.load_stencil, bg="#2196f3", fg="white", font=("Arial", 7)).pack(side="left", padx=2)
        tk.Checkbutton(toolbar, text="GHOST SHOW", variable=self.show_stencil, command=self.toggle_stencil, bg="#222", fg="#00bcd4", selectcolor="#222").pack(side="left", padx=5)
        
        self.lbl_probe = tk.Label(toolbar, text="MOUSE OFF-MAP", bg="#222", fg="#fff", font=("Arial", 8, "bold"), width=30, anchor="w")
        self.lbl_probe.pack(side="left", padx=10)

        b_frame = tk.Frame(toolbar, bg="#222"); b_frame.pack(side="left", padx=20)
        for cat, modes in self.biome_categories.items():
            menubutton = tk.Menubutton(b_frame, text=cat.upper(), bg="#333", fg="#00bcd4", font=("Arial", 8, "bold"), relief="flat")
            menu = tk.Menu(menubutton, tearoff=0, bg="#222", fg="#ccc", activebackground="#00bcd4")
            menubutton.config(menu=menu)
            for m in modes:
                # Use a closure to capture m correctly
                def make_cmd(mode_str): return lambda: setattr(self, 'brush_mode', mode_str)
                menu.add_command(label=m.upper(), command=make_cmd(m))
            menubutton.pack(side="left", padx=2)
        
        tk.Label(toolbar, text="Size:", bg="#222", fg="#888", font=("Arial", 8)).pack(side="left", padx=(10, 2))
        bsize = tk.Scale(toolbar, from_=1, to=15, orient="horizontal", bg="#222", fg="#fff", troughcolor="#333", length=100, showvalue=False, command=lambda v: setattr(self, 'brush_radius', int(v)))
        bsize.set(self.brush_radius); bsize.pack(side="left", padx=5)
        
        main_frame = tk.Frame(self.root, bg="#111"); main_frame.pack(fill="both", expand=True)
        cp_container = tk.Frame(main_frame, bg="#181818", padx=5); cp_container.pack(side="left", fill="y", padx=5, pady=10)
        cp_canvas = tk.Canvas(cp_container, bg="#181818", width=180, highlightthickness=0); cp_vscroll = tk.Scrollbar(cp_container, orient="vertical", command=cp_canvas.yview)
        cp = tk.Frame(cp_canvas, bg="#181818", padx=10); cp_canvas.create_window((0,0), window=cp, anchor="nw")
        cp_canvas.configure(yscrollcommand=cp_vscroll.set); cp_canvas.pack(side="left", fill="both", expand=True); cp_vscroll.pack(side="right", fill="y")
        
        sliders = [("Sea Level", "sea_level"), ("Aridity", "aridity"), ("Peak Intensity", "peak_intensity"), ("Mtn Cluster Count", "mtn_clusters"), ("Mtn Cluster Size", "mtn_scale"), ("Rain Level", "moisture_level"), ("Inlet Depth", "inlet_depth"), ("Hub Growth", "city_hubs"), ("Road Vines", "road_vines")]
        for label, key in sliders:
            tk.Label(cp, text=label, bg="#181818", fg="#888", font=("Arial", 8)).pack(anchor="w")
            scl = tk.Scale(cp, from_=0.0, to=1.0, resolution=0.1, orient="horizontal", bg="#181818", fg="#ccc", troughcolor="#333", activebackground="#00bcd4", command=lambda v, k=key: self.update_weight(k, v)); scl.set(self.weights[key]); scl.pack(fill="x", pady=(0, 10))
        
        # LEGEND SECTION
        tk.Label(cp, text="--- TERRAIN LEGEND ---", bg="#181818", fg="#00bcd4", font=("Arial", 8, "bold")).pack(pady=(20, 5))
        legend_items = [("OCEAN", "ocean"), ("WATR", "water"), ("FORST", "forest"), ("DESRT", "desert"), ("PLNS", "plains"), ("MOUN", "mountain"), ("PEAK", "peak"), ("ROAD", "road")]
        for name, key in legend_items:
            f = tk.Frame(cp, bg="#181818")
            f.pack(fill="x")
            tk.Label(f, text=" ", bg=COLOR_MAP.get(key, "#000"), width=2).pack(side="left", padx=2)
            tk.Label(f, text=name, bg="#181818", fg="#aaa", font=("Arial", 7)).pack(side="left")

        cp_canvas.configure(scrollregion=cp_canvas.bbox("all"))

        canvas_frame = tk.Frame(main_frame, bg="black"); canvas_frame.pack(side="left", padx=5, pady=10, fill="both", expand=True)
        h_s = tk.Scrollbar(canvas_frame, orient="horizontal"); v_s = tk.Scrollbar(canvas_frame, orient="vertical")
        self.canvas = tk.Canvas(canvas_frame, bg="black", highlightthickness=0, xscrollcommand=h_s.set, yscrollcommand=v_s.set)
        h_s.config(command=self.canvas.xview); v_s.config(command=self.canvas.yview)
        h_s.pack(side="bottom", fill="x"); v_s.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        
        self.canvas.bind("<Button-1>", self.on_canvas_press); self.canvas.bind("<B1-Motion>", self.on_canvas_drag); self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release); self.canvas.bind("<MouseWheel>", self.on_zoom)
        self.canvas.bind("<Motion>", self.on_canvas_move)
        
        self.lbl_status = tk.Label(self.root, text="V14.0 ARCHITECT READY", bg="#222", fg="#00bcd4", font=("Arial", 9, "bold"), anchor="w", padx=10)
        self.lbl_status.pack(side="bottom", fill="x")
        
        self.draw_map(); self.root.mainloop()

if __name__ == "__main__":
    architect = AethelgardArchitect()
    architect.run_gui()
