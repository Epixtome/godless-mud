from logic.core import event_engine

def mob_ai(game):
    """Periodic tick for Mob AI and mechanics."""
    for room in game.world.rooms.values():
        for mob in room.monsters:
            if getattr(mob, 'pending_death', False):
                continue
            event_engine.dispatch("mob_tick", game=game, mob=mob, tick=game.tick_count)
