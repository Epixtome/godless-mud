import random
import logging
from models import Monster

logger = logging.getLogger("GodlessMUD")

# --- Configuration ---
SPAWN_TABLES = {
    "forest": [("wolf", 8), ("bear", 4), ("bandit", 3), ("feral_hog", 5), ("dryad", 1), ("sprite", 2)],
    "cave":   [("bat", 8), ("slime", 4), ("troll", 1), ("earth_elemental", 2), ("giant_beetle", 4)],
    "crypt":  [("skeleton", 8), ("zombie", 6), ("ghost", 2), ("lich", 0.5), ("wraith", 3)],
    "city":   [("citizen", 8), ("guard", 4), ("thief", 5), ("beggar", 3), ("merchant", 2)],
    "dungeon": [("goblin", 8), ("orc", 4), ("shaman", 2), ("minotaur", 1), ("mimic", 1)],
    "default": [("rat", 5), ("stray_cat", 2), ("moth", 3)]
}

TERRAIN_TABLES = {
    "forest": [("wolf", 6), ("deer", 8), ("owl", 3)],
    "mountain": [("goat", 6), ("eagle", 4), ("griffin", 0.5)],
    "swamp": [("snake", 6), ("toad", 8), ("will_o_wisp", 2)],
    "water": [("fish", 12), ("shark", 1), ("octopus", 2)],
    "road": [("traveler", 3), ("bandit", 2), ("merchant_caravan", 1), ("messenger", 2), ("broken_wagon", 0.5)]
}

def get_mob_pool(zone_id, terrain):
    pool = []
    zone_id = zone_id.lower() if zone_id else ""
    terrain = terrain.lower() if terrain else ""

    for key, mobs in SPAWN_TABLES.items():
        if key in zone_id:
            pool.extend(mobs)

    if terrain in TERRAIN_TABLES:
        pool.extend(TERRAIN_TABLES[terrain])

    if not pool:
        pool = SPAWN_TABLES["default"]
        
    return pool

def select_mob_prototype(game, pool):
    if not pool: return None, None

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

    if selected_fragment in game.world.monsters:
        return selected_fragment, game.world.monsters[selected_fragment]

    candidates = [
        (mid, m) for mid, m in game.world.monsters.items() 
        if selected_fragment in mid.lower() or selected_fragment in m.name.lower()
    ]
    
    if candidates:
        return random.choice(candidates)

    return None, None

def populate_world(game):
    logger.info("Spawner: Populating world based on region data...")
    count = 0
    unique_registry = getattr(game.world, 'unique_registry', {})
    
    for room in game.world.rooms.values():
        # Blueprint Mobs
        # These are handled by the loader on zone load, but we can verify here
        
        # Ambient Spawning
        if len(room.monsters) >= 2:
            continue
            
        if random.random() > 0.08:
            continue
            
        pool = get_mob_pool(room.zone_id, room.terrain)
        real_id, proto = select_mob_prototype(game, pool)
        
        if proto:
            # UNIQUE Gating:
            # Prevent duplicate unique bosses/mobs
            if "UNIQUE" in getattr(proto, 'tags', []):
                status = unique_registry.get(real_id, {}).get('status', 'available')
                if status != 'available':
                    continue # Already exists or is on cooldown
                
                # Mark as alive in registry
                unique_registry[real_id] = {"status": "alive", "room_id": room.id}
            
            new_mob = Monster(
                proto.name, proto.description, proto.hp, proto.damage, 
                tags=proto.tags, max_hp=proto.max_hp, prototype_id=real_id
            )
            
            new_mob.room = room
            new_mob.game = game
            new_mob.quests = proto.quests
            new_mob.can_be_companion = proto.can_be_companion
            new_mob.resources = {"stamina": 100, "concentration": 100, "mana": 100}
            new_mob.cooldowns = {}
            new_mob.active_class = None
            new_mob.temporary = True
            
            room.monsters.append(new_mob)
            count += 1
            
    logger.info(f"Spawner: Instantiated {count} ambient mobs.")
