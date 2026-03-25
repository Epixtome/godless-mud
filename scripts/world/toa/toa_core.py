import os
import json
import time

class TOAState:
    """[TOA V20.0] The high-performance, async-first state manager for Omnipresent Architecture."""
    def __init__(self, width=125, height=125):
        self.width = width
        self.height = height
        
        # 1. THE INTENT LAYERS (Floating point precision for smooth negotiation)
        self.bias_elev = [[0.0 for _ in range(width)] for _ in range(height)]
        self.bias_moist = [[0.0 for _ in range(width)] for _ in range(height)]
        self.bias_volume = [[0.0 for _ in range(width)] for _ in range(height)] # Intensity of intent
        
        # 2. THE SEMANTIC INTENT (Identity storage)
        self.bias_biomes = [[None for _ in range(width)] for _ in range(height)]
        self.bias_landmarks = [[None for _ in range(width)] for _ in range(height)]
        self.bias_roads = [[0 for _ in range(width)] for _ in range(height)]
        
        # 3. INTERACTION LAYERS (Gameplay metadata)
        self.bias_cr = [[0.5 for _ in range(width)] for _ in range(height)]
        self.bias_spawn = [[0.5 for _ in range(width)] for _ in range(height)]
        
        # 4. THE NEGOTIATED REALITY (The current result)
        self.grid = [["ocean" for _ in range(width)] for _ in range(height)]
        self.debug_stats = {"elev": None, "moist": None}
        
        # 5. CONFIGURATION
        self.weights = {
            "sea_level": 0.5, "aridity": 0.5, "peak_intensity": 1.0, "mtn_clusters": 0.5,
            "mtn_scale": 0.5, "moisture_level": 0.5, "land_density": 0.6, "biome_isolation": 0.5,
            "erosion_scale": 0.2, "fertility_rate": 1.0, "blossom_speed": 1.0, "melting_point": 0.0,
            "designer_authority": 0.5, "seed": str(int(time.time()))
        }
        
        # [V20.0] Undo/Redo Storage
        self.undo_stack = []

    def apply_brush(self, x, y, mode, volume=0.1):
        """[V20.0] Additive intent injection (Spray-paint style)."""
        if x < 0 or x >= self.width or y < 0 or y >= self.height: return
        
        # Volume accumulation (Loudness)
        self.bias_volume[y][x] = min(5.0, self.bias_volume[y][x] + volume)
        
        # SEMANTIC NUANCE
        if mode == "water":
            self.bias_elev[y][x] = max(-1.0, self.bias_elev[y][x] - volume)
        elif mode == "peak":
            self.bias_elev[y][x] = min(1.0, self.bias_elev[y][x] + volume)
        elif mode == "moist":
            self.bias_moist[y][x] = min(1.0, self.bias_moist[y][x] + volume)
        elif mode == "dry":
            self.bias_moist[y][x] = max(-1.0, self.bias_moist[y][x] - volume)
        elif mode == "road":
            self.bias_roads[y][x] = 1
        elif mode == "erase":
            self.bias_volume[y][x] = 0.0
            self.bias_elev[y][x] = 0.0
            self.bias_moist[y][x] = 0.0
            self.bias_biomes[y][x] = None
            self.bias_roads[y][x] = 0
        else:
            # Snap to biome identity (The '@' logic: The user wants exactly this)
            self.bias_biomes[y][x] = mode 

    def push_undo_snap(self):
        """Captures surgical bias snapshot."""
        snap = {
            "elev": [row[:] for row in self.bias_elev],
            "moist": [row[:] for row in self.bias_moist],
            "volume": [row[:] for row in self.bias_volume],
            "biomes": [row[:] for row in self.bias_biomes],
            "roads": [row[:] for row in self.bias_roads]
        }
        self.undo_stack.append(snap)
        if len(self.undo_stack) > 30: self.undo_stack.pop(0)

    def to_json(self):
        """Prepares a non-destructive TOA stencil."""
        return {
            "version": "20.0",
            "weights": self.weights,
            "bias_elev": self.bias_elev,
            "bias_moist": self.bias_moist,
            "bias_volume": self.bias_volume,
            "bias_biomes": self.bias_biomes,
            "bias_roads": self.bias_roads,
            "bias_cr": self.bias_cr,
            "bias_spawn": self.bias_spawn,
            "width": self.width,
            "height": self.height
        }
