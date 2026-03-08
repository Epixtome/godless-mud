from logic.core import status_effects_engine

def monitor_terrain(game):
    """Applies terrain-based effects to entities."""
    if game.tick_count % 10 != 0:
        return

    TERRAIN_EFFECTS = {
        "water": "wet",
        "lava": "burning",
        "mud": "slowed",
        "poison_gas": "poisoned"
    }

    for room in game.world.rooms.values():
        terrain = getattr(room, 'terrain', None)
        if terrain in TERRAIN_EFFECTS:
            status_id = TERRAIN_EFFECTS[terrain]
            for entity in room.players + room.monsters:
                status_effects_engine.apply_effect(entity, status_id, 3)
