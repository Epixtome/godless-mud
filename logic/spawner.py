

import random
import logging
from models import Monster

logger = logging.getLogger("GodlessMUD")

# --- Configuration ---
# Define mob pools based on Zone IDs (partial match) or Terrain types.
# Format: "key": [("mob_id_fragment", weight), ...]
# The system will search for mobs matching the fragment if an exact ID isn't found.

SPAWN_TABLES = {
    # Zone ID Matches (Thematic)
    "forest": [("wolf", 10), ("bear", 5), ("bandit", 5), ("spider", 3)],
    "cave":   [("bat", 10), ("slime", 5), ("troll", 2)],
    "crypt":  [("skeleton", 10), ("zombie", 8), ("ghost", 2)],
    "city":   [("citizen", 10), ("guard", 5), ("rat", 5)],
    "dungeon": [("goblin", 10), ("orc", 5), ("shaman", 2)],
    
    # Fallback / Generic
    "default": [("rat", 10), ("wild_dog", 5)]
}

TERRAIN_TABLES = {
    "forest": [("wolf", 8), ("deer", 5)],
    "mountain": [("goat", 5), ("eagle", 3)],
    "swamp": [("snake", 8), ("crocodile", 3)],
    "water": [("fish", 10), ("shark", 1)],
    "road": [("traveler", 5), ("bandit", 2)]
}

def get_mob_pool(zone_id, terrain):
    """
    Constructs a weighted pool of mobs based on the environment.
    """
    pool = []
    zone_id = zone_id.lower() if zone_id else ""
    terrain = terrain.lower() if terrain else ""

    # 1. Zone Specifics (Highest Priority)
    for key, mobs in SPAWN_TABLES.items():
        if key in zone_id:
            pool.extend(mobs)

    # 2. Terrain Specifics
    if terrain in TERRAIN_TABLES:
        pool.extend(TERRAIN_TABLES[terrain])

    # 3. Fallback
    if not pool:
        pool = SPAWN_TABLES["default"]
        
    return pool

def select_mob_prototype(game, pool):
    """
    Selects a mob ID from the pool and resolves it to a real Prototype from the DB.
    """
    if not pool: return None, None

    # Weighted Random Selection
    total_weight = sum(w for m, w in pool)
    r = random.uniform(0, total_weight)
    current = 0
    selected_fragment = None
    
    for m_frag, weight in pool:
        current += weight
        if r <= current:
            selected_fragment = m_frag
            break
    
    if not selected_fragment:
        return None, None

    # Resolve Fragment to Real Prototype
    # 1. Try Exact Match
    if selected_fragment in game.world.monsters:
        return selected_fragment, game.world.monsters[selected_fragment]

    # 2. Fuzzy Match (Find any mob ID containing the fragment)
    candidates = [
        (mid, m) for mid, m in game.world.monsters.items() 
        if selected_fragment in mid.lower() or selected_fragment in m.name.lower()
    ]
    
    if candidates:
        return random.choice(candidates)

    return None, None

def populate_world(game):
    """
    Fills the world with life based on Zone and Terrain data.
    Run this after loading static spawns.
    """
    logger.info("Spawner: Populating world based on region data...")
    count = 0
    
    for room in game.world.rooms.values():
        # 1. Density Check
        # Don't overpopulate rooms that already have static mobs
        if len(room.monsters) >= 2:
            continue
            
        # 2. Spawn Chance (e.g., 15% chance per empty room)
        if random.random() > 0.15:
            continue
            
        # 3. Determine Pool
        pool = get_mob_pool(room.zone_id, room.terrain)
        
        # 4. Select and Spawn
        real_id, proto = select_mob_prototype(game, pool)
        
        if proto:
            # Instantiate (Clone from Prototype)
            new_mob = Monster(
                proto.name, proto.description, proto.hp, proto.damage, 
                tags=proto.tags, max_hp=proto.max_hp, prototype_id=real_id
            )
            
            # Hydrate References
            new_mob.room = room
            new_mob.game = game
            new_mob.quests = proto.quests
            new_mob.can_be_companion = proto.can_be_companion
            new_mob.resources = {"stamina": 100, "concentration": 100, "mana": 100}
            new_mob.cooldowns = {}
            new_mob.active_class = None
            new_mob.temporary = True
            
            # Add to Room
            room.monsters.append(new_mob)
            count += 1
            
    logger.info(f"Spawner: Instantiated {count} ambient mobs.")
