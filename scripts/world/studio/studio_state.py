import os
import json
import random
import time
import glob
import math

# Relative imports from the parent directory
import architect_logic as core
import architect_data as data
import studio_config

class StudioState:
    def __init__(self):
        self.width = studio_config.DEFAULT_WIDTH
        self.height = studio_config.DEFAULT_HEIGHT
        self.offset_x = studio_config.OFFSET_X
        self.offset_y = studio_config.OFFSET_Y
        self.offset_z = studio_config.OFFSET_Z
        self.zone_prefix = studio_config.ZONE_PREFIX
        
        # Grid Data
        self.grid = [["ocean" for _ in range(self.width)] for _ in range(self.height)]
        
        # Layer Buffers - The user's INTENT layers
        self.bias_elev = [[0.0 for _ in range(self.width)] for _ in range(self.height)]
        self.bias_moist = [[0.0 for _ in range(self.width)] for _ in range(self.height)]
        self.bias_roads = [[0 for _ in range(self.width)] for _ in range(self.height)]
        self.bias_biomes = [[None for _ in range(self.width)] for _ in range(self.height)]
        self.bias_volume = [[0.0 for _ in range(self.width)] for _ in range(self.height)] # [V17.4] Intensity of Intent
        
        # [V15.0 NEW] Difficulty & Interaction Buffers
        self.bias_cr = [[0.5 for _ in range(self.width)] for _ in range(self.height)] # 0.0 to 1.0 (scaling to Lv 1-100)
        self.bias_spawn = [[0.5 for _ in range(self.width)] for _ in range(self.height)] # Density of mobs
        self.bias_peaks = [[0.0 for _ in range(self.width)] for _ in range(self.height)] # Ridge / Spine intent
        self.bias_inlets = [[0.0 for _ in range(self.width)] for _ in range(self.height)] # Coastal carving points
        self.bias_landmarks = [[None for _ in range(self.width)] for _ in range(self.height)] # Shrines, Ruins, etc.
        self.sovereignty_pins = [] # List of {x, y, kingdom, strength}
        
        # [V16.0] OBSERVABILITY & TELEMETRY 
        self.phase_grids = {} # key -> grid deepcopy
        self.debug_stats = {"elev": None, "moist": None} # raw maps

        # Weights Configuration
        self.weights = studio_config.DEFAULT_WEIGHTS.copy()
        self.active_config = data.load_config() # map_config.json
        
        # [V17.9] History Buffers
        self.undo_stack = []
        self.redo_stack = []

    def reset_grid(self):
        self.grid = [["ocean" for _ in range(self.width)] for _ in range(self.height)]

    def clear_all_buffers(self):
        """Purges all user intent layers for a clean slate."""
        self.bias_elev = [[0.0 for _ in range(self.width)] for _ in range(self.height)]
        self.bias_moist = [[0.0 for _ in range(self.width)] for _ in range(self.height)]
        self.bias_roads = [[0 for _ in range(self.width)] for _ in range(self.height)]
        self.bias_biomes = [[None for _ in range(self.width)] for _ in range(self.height)]
        self.bias_cr = [[0.5 for _ in range(self.width)] for _ in range(self.height)]
        self.bias_spawn = [[0.5 for _ in range(self.width)] for _ in range(self.height)]
        self.bias_peaks = [[0.0 for _ in range(self.width)] for _ in range(self.height)]
        self.bias_inlets = [[0.0 for _ in range(self.width)] for _ in range(self.height)]
        self.bias_landmarks = [[None for _ in range(self.width)] for _ in range(self.height)]
        self.sovereignty_pins = []

    def full_generation_pass(self):
        """Orchestrates the multi-phase generation logic from core engines."""
        has_intent = any([
            any(any(row) for row in self.bias_peaks),
            any(any(row) for row in self.bias_inlets),
            any(any(row) for row in self.bias_landmarks if any(r is not None for r in row)),
            len(self.sovereignty_pins) > 0
        ])
        
        mode_str = "Intent-Driven" if has_intent else "Procedural Baseline"
        print(f"--- [V17.4] Running {mode_str} Simulation ({self.offset_x}, {self.offset_y}) ---")
        
        # 1. Seed Handling (Auto-rotate if blank)
        s_val = self.weights.get("seed", "")
        if not s_val: 
            s_val = int(time.time() * 1000) % 1000000
            self.weights["seed"] = str(s_val) # Save back to UI
        else:
            try: s_val = int(s_val); 
            except: s_val = hash(str(s_val)) % 1000000
            
        random.seed(s_val); self.active_config["seed"] = s_val
        
        # 2. Sync Config with Weights and Buffers
        self.active_config.update(self.weights)
        self.active_config["designer_authority"] = self.weights.get("designer_authority", 0.0) # [V17.4] New weight
        self.active_config["bias_elev"] = self.bias_elev
        self.active_config["bias_moist"] = self.bias_moist
        self.active_config["bias_roads"] = self.bias_roads
        self.active_config["bias_biomes"] = self.bias_biomes
        self.active_config["bias_volume"] = self.bias_volume # [V17.4] Pass volume buffer
        self.active_config["bias_cr"] = self.bias_cr
        self.active_config["bias_spawn"] = self.bias_spawn
        self.active_config["bias_peaks"] = self.bias_peaks
        self.active_config["bias_inlets"] = self.bias_inlets
        self.active_config["bias_landmarks"] = self.bias_landmarks

        # 3. Purge Stale Export Shards
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        zone_dir = os.path.join(base_dir, "data", "zones")
        stale_shards = glob.glob(os.path.join(zone_dir, f"{self.zone_prefix}*.json"))
        for f in stale_shards: 
            try: os.remove(f)
            except: pass
            
        # 4. Kingdom Hub Positioning (Intent Pins Only)
        k_ids = list(self.active_config.get("kingdoms", {}).keys())
        for pin in self.sovereignty_pins:
            # Match pin to kingdom index if possible, or just assign
            # For now, just pass the pins as a list in config for the scouter
            pass
        self.active_config["sovereignty_pins"] = self.sovereignty_pins
        
        # Centers are now handled dynamically in architect_infrastructure based on pins
        pass

        # 5. [ENGINE CALLS] - The Shared Pipe (V16.0 Phase Snapshots)
        self.phase_grids = {}
        
        # A. Climate (Biomatic Foundation)
        res = core.run_climate_pass(self.grid, self.width, self.height, self.active_config)
        self.debug_stats["elev"] = res.get("elev_map")
        self.debug_stats["moist"] = res.get("moist_map")
        self.phase_grids["Baseline"] = [row[:] for row in self.grid]
        
        # B. Tectonics (Mountains & Landmass)
        core.run_phase_0_logic(self.grid, self.width, self.height, self.active_config) 
        core.run_phase_1_logic(self.grid, self.width, self.height, self.active_config) 
        self.phase_grids["Tectonics"] = [row[:] for row in self.grid]
        
        # C. Hydrology (Rivers & Gulfs)
        core.run_phase_1_5_logic(self.grid, self.width, self.height, self.active_config) 
        grid_meta = {"elev_map": self.debug_stats["elev"]} 
        core.run_phase_2_logic(self.grid, self.width, self.height, self.active_config, grid_meta) 
        self.phase_grids["Hydrology"] = [row[:] for row in self.grid]
        
        # D. Infrastructure (Civ & Urban Growth)
        core.run_phase_3_logic(self.grid, self.width, self.height, self.active_config) 
        self.phase_grids["Civ"] = [row[:] for row in self.grid]
        
        # E. Final (Smoothing & Landmark Decoration)
        core.run_phase_4_logic(self.grid, self.width, self.height)              
        core.run_phase_5_logic(self.grid, self.width, self.height, self.active_config) 
        self.phase_grids["Final"] = [row[:] for row in self.grid]
        
        core.run_phase_6_export(
            self.grid, self.width, self.height, self.offset_x, self.offset_y, self.offset_z, 
            self.zone_prefix, self.active_config
        )
        print(f"--- [V16.0] Simulation Ready (Snapshots Loaded) ---")
        
    def live_negotiation(self, roi=None):
        """[V17.9] SURGICAL BIOMATIC REMAP: Updates only specific tiles for performance."""
        # Sync weights
        self.active_config.update(self.weights)
        
        # Determine targeting (ROI or Full)
        coords = roi if roi else [(x, y) for y in range(self.height) for x in range(self.width)]
        
        base_elev = self.debug_stats.get("elev")
        base_moist = self.debug_stats.get("moist")
        
        for x, y in coords:
            # 1. Base Values (Reality Foundation)
            e_val = base_elev[y][x] if base_elev else 0.5 
            m_val = base_moist[y][x] if base_moist else 0.5
            
            # 2. Add Biases
            e_val = max(0.0, min(1.0, e_val + self.bias_elev[y][x]))
            m_val = max(0.0, min(1.0, m_val + self.bias_moist[y][x]))
            
            # 3. Handle Semantic Overrides
            p_biome = self.bias_biomes[y][x]
            if p_biome in core.run_climate_pass.__globals__.get('BIOME_TARGETS', {}):
                # Drift maps based on biome stamp if needed, but for 'Conditions' we let matrix decide
                pass
            
            # 4. Final Remap
            self.grid[y][x] = core.get_biome_from_matrix(e_val, m_val)
            
            # 5. Inject into ALL snapshots to keep views in sync during live work
            for phase in self.phase_grids:
                self.phase_grids[phase][y][x] = self.grid[y][x]

    def apply_brush(self, x, y, mode, power=0.15):
        """[V17.0] Core painting logic for state buffers."""
        if mode == "none": return
        
        # 1. INFRASTRUCTURE & LANDMARKS
        if mode == "road": self.bias_roads[y][x] = 1 
        elif mode == "bridge": self.bias_roads[y][x] = 2 # Distinct bridge flag
        elif mode == "inlet": self.bias_inlets[y][x] = 1.0
        elif mode == "volcano": 
            self.bias_peaks[y][x] = 1.0
            self.bias_biomes[y][x] = "peak"
            
        # 2. TOPOGRAPHICAL BIASES (Incremental)
        elif mode in ["peak", "mountain", "high_mountain"]:
            self.bias_elev[y][x] = min(1.0, self.bias_elev[y][x] + power)
            self.bias_biomes[y][x] = mode
            if mode == "peak": self.bias_peaks[y][x] = min(1.0, self.bias_peaks[y][x] + power * 2)
        elif mode in ["water", "ocean", "lake"]:
            self.bias_elev[y][x] = max(-1.0, self.bias_elev[y][x] - power)
            self.bias_biomes[y][x] = mode
        elif mode == "desert":
            self.bias_moist[y][x] = max(-1.0, self.bias_moist[y][x] - power)
            self.bias_biomes[y][x] = mode
        elif mode in ["forest", "dense_forest", "swamp"]:
            self.bias_moist[y][x] = min(1.0, self.bias_moist[y][x] + power)
            self.bias_biomes[y][x] = mode
            
        # 3. INTERACTION LAYERS
        elif mode == "cr":
            self.bias_cr[y][x] = min(1.0, self.bias_cr[y][x] + power)
        elif mode == "mob":
            self.bias_spawn[y][x] = min(1.0, self.bias_spawn[y][x] + power)
        
        # 4. LANDMARKS (Atomic stamp)
        elif mode in ["shrine", "monument", "tower", "ruins", "barrows", "city"]:
            self.bias_landmarks[y][x] = mode
            
        # 5. [V17.9] SEMANTIC CONDITIONS (Nudges)
        elif mode == "dry":
            self.bias_moist[y][x] = max(-1.0, self.bias_moist[y][x] - power)
        elif mode == "moist":
            self.bias_moist[y][x] = min(1.0, self.bias_moist[y][x] + power)
        elif mode == "rise":
            self.bias_elev[y][x] = min(1.0, self.bias_elev[y][x] + power)
        elif mode == "sink":
            self.bias_elev[y][x] = max(-1.0, self.bias_elev[y][x] - power)
            
        else:
            # Catch-all for basic biomes (plains, grass, wasteland)
            self.bias_biomes[y][x] = mode
            
        # [V17.4] INCREMENTAL VOLUME (Loudness)
        self.bias_volume[y][x] = min(5.0, self.bias_volume[y][x] + power)

    def push_undo(self):
        """Captures a snapshot of the current bias state."""
        snapshot = {
            "elev": [row[:] for row in self.bias_elev],
            "moist": [row[:] for row in self.bias_moist],
            "biomes": [row[:] for row in self.bias_biomes],
            "volume": [row[:] for row in self.bias_volume]
        }
        self.undo_stack.append(snapshot)
        if len(self.undo_stack) > 20: self.undo_stack.pop(0)
        self.redo_stack.clear()

    def pop_undo(self):
        if not self.undo_stack: return False
        # Save current to redo
        snapshot = {
            "elev": [row[:] for row in self.bias_elev],
            "moist": [row[:] for row in self.bias_moist],
            "biomes": [row[:] for row in self.bias_biomes],
            "volume": [row[:] for row in self.bias_volume]
        }
        self.redo_stack.append(snapshot)
        
        last = self.undo_stack.pop()
        self.bias_elev = last["elev"]
        self.bias_moist = last["moist"]
        self.bias_biomes = last["biomes"]
        self.bias_volume = last["volume"]
        return True

    # --- Persistance ---
    def save_stencil(self, path=None):
        if not path:
            # 4 levels up: studio_state.py -> studio -> world -> scripts -> root
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            path = os.path.join(base_dir, "scripts", "world", "studio", f"v{studio_config.VERSION}_intent.stencil")
        
        data = {
            "version": studio_config.VERSION,
            "elev": self.bias_elev, 
            "moist": self.bias_moist, 
            "roads": self.bias_roads,
            "biomes": self.bias_biomes,
            "cr": self.bias_cr,
            "spawn": self.bias_spawn,
            "peaks": self.bias_peaks,
            "inlets": self.bias_inlets,
            "volume": self.bias_volume,
            "landmarks": self.bias_landmarks,
            "pins": self.sovereignty_pins
        }
        with open(path, "w") as f: json.dump(data, f)
        return path

    def load_stencil(self, path=None):
        if not path:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            path = os.path.join(base_dir, "scripts", "world", "studio", f"v{studio_config.VERSION}_intent.stencil")
            
        if os.path.exists(path):
            with open(path, "r") as f:
                data = json.load(f)
                self.bias_elev = data.get("elev", self.bias_elev)
                self.bias_moist = data.get("moist", self.bias_moist)
                self.bias_roads = data.get("roads", self.bias_roads)
                self.bias_biomes = data.get("biomes", self.bias_biomes)
                self.bias_cr = data.get("cr", self.bias_cr)
                self.bias_spawn = data.get("spawn", self.bias_spawn)
                self.bias_peaks = data.get("peaks", self.bias_peaks)
                self.bias_inlets = data.get("inlets", self.bias_inlets)
                self.bias_volume = data.get("volume", [[0.0 for _ in range(self.width)] for _ in range(self.height)])
                self.bias_landmarks = data.get("landmarks", self.bias_landmarks)
                self.sovereignty_pins = data.get("pins", self.sovereignty_pins)
            return True
        return False
