"""
logic/core/systems/influence_service.py
The math engine for the Influence Tide.
Calculates Sovereignty and Security Ratings based on Shrine emitters.
"""
import math
import json
import os
import logging
from models import Shrine

logger = logging.getLogger("GodlessMUD")

class InfluenceService:
    _instance = None
    
    def __init__(self):
        self.shrines = {} # id -> Shrine
        self.cached_influence = {} # (x, y, z) -> (dominant_kingdom, strength)
        self.cached_security = {} # (x, y, z) -> security_rating
        
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def pulse(self, game):
        """
        Periodic task to warm the influence cache for active player locations.
        Helps keep the 'influence' command and defensive checks snappy.
        """
        active_coords = set()
        for p in game.players.values():
            if p.room:
                active_coords.add((p.room.x, p.room.y, p.room.z))
                
        for coords in active_coords:
            self.get_influence(*coords)
            self.get_security_rating(*coords)

    def initialize(self, world=None):
        """Loads shrines from data and registers them for calculation."""
        path = "data/shrines.json"
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    data = json.load(f)
                    if "shrines" in data:
                        for s_id, s_data in data["shrines"].items():
                            shrine = Shrine.from_dict(s_data)
                            self.shrines[s_id] = shrine
                logger.info(f"InfluenceService initialized with {len(self.shrines)} shrines.")
            except Exception as e:
                logger.error(f"Failed to load shrines from {path}: {e}")
        else:
            logger.warning(f"Shrine registry {path} not found.")

        self.clear_cache()

    def save_shrines(self):
        """Persists the live state of all shrines back to JSON."""
        path = "data/shrines.json"
        try:
            shrine_data = {s_id: s.to_dict() for s_id, s in self.shrines.items()}
            with open(path, "w", encoding='utf-8') as f:
                json.dump({"shrines": shrine_data}, f, indent=4)
            logger.info(f"InfluenceService persisted {len(self.shrines)} shrines to {path}.")
        except Exception as e:
            logger.error(f"Failed to save shrines: {e}")

    def register_shrine(self, shrine):
        self.shrines[shrine.id] = shrine
        self.clear_cache()

    def clear_cache(self):
        self.cached_influence.clear()
        self.cached_security.clear()

    def get_influence(self, x, y, z=0):
        """
        Calculates the influence tide at coordinates.
        Power = Potency - (Distance * Decay)
        """
        coord_key = (x, y, z)
        if coord_key in self.cached_influence:
            return self.cached_influence[coord_key]

        influence_sums = {"light": 0.0, "dark": 0.0, "instinct": 0.0}
        
        for shrine in self.shrines.values():
            if shrine.coords[2] != z: continue # Only same Z-plane
            
            dist = math.sqrt((shrine.coords[0] - x)**2 + (shrine.coords[1] - y)**2)
            power = max(0, shrine.potency - (dist * shrine.decay))
            
            if shrine.captured_by in influence_sums:
                influence_sums[shrine.captured_by] += power

        # Determine dominant kingdom
        dominant = "neutral"
        max_power = 0.0
        
        for kingdom, power in influence_sums.items():
            if power > max_power:
                max_power = power
                dominant = kingdom

        self.cached_influence[coord_key] = (dominant, max_power)
        return dominant, max_power

    def get_security_rating(self, x, y, z=0):
        """
        Calculates security status (1.0 to 0.0).
        1.0: Capital (Invulnerable, lethal guardians)
        0.8 - 0.5: Outposts (Sentinels)
        0.4 - 0.0: Frontier/Void
        """
        coord_key = (x, y, z)
        if coord_key in self.cached_security:
            return self.cached_security[coord_key]

        # Security is primarily driven by proximity to the nearest CAPITAL shrine
        max_security = 0.0
        for shrine in self.shrines.values():
            if shrine.coords[2] != z: continue
            
            dist = math.sqrt((shrine.coords[0] - x)**2 + (shrine.coords[1] - y)**2)
            
            if shrine.is_capital:
                # 1.0 at 0 distance, decays to 0.5 over a large range
                sec = max(0.0, 1.0 - (dist / 100.0))
                sec = max(sec, 0.45) if dist < 150 else sec # Hold Mid-Sec for a while
            else: # Outpost
                # 0.8 at 0 distance, decays quickly
                sec = max(0.0, 0.8 - (dist / 25.0))
            
            if sec > max_security:
                max_security = sec

        rating = round(max_security, 1)
        self.cached_security[coord_key] = rating
        return rating

    def get_security_label(self, rating):
        if rating >= 1.0: return "High (Capital)"
        if rating >= 0.5: return "Mid (Outpost)"
        if rating >= 0.1: return "Low (Frontier)"
        return "Null (Void)"
