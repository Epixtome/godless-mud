from logic.core import effects

def monitor_terrain(game):
    """Applies terrain-based effects to entities efficiently."""
    if game.tick_count % 10 != 0:
        return

    TERRAIN_EFFECTS = {
        "water": "wet",
        "lava": "burning",
        "mud": "slowed",
        "poison_gas": "poisoned"
    }

    # Optimization: Only iterate over rooms with entities
    for room in game.world.rooms.values():
        if not (room.players or room.monsters):
            continue
            
        terrain = getattr(room, 'terrain', None)
        if terrain in TERRAIN_EFFECTS:
            status_id = TERRAIN_EFFECTS[terrain]
            for entity in room.players + room.monsters:
                effects.apply_effect(entity, status_id, 15)
