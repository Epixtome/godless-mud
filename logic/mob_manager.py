import random
import logging
from models import Monster
from utilities.colors import Colors
from logic.core import event_engine
from logic.constants import Tags

logger = logging.getLogger("GodlessMUD")

def spawn_mob(room, mob_data, game):
    """Instantiates a mob from data (ID string or dict) and adds to room."""
    if isinstance(mob_data, dict):
        mob_id = mob_data.get('id')
        deltas = mob_data
    else:
        mob_id = mob_data
        deltas = {}

    if mob_id not in game.world.monsters:
        logger.warning(f"Cannot spawn unknown mob ID: {mob_id}")
        return

    if mob_id in game.world.monsters:
        proto = game.world.monsters[mob_id]
        # Clone prototype
        instance = Monster(proto.name, proto.description, proto.hp, proto.damage, 
                           proto.tags, proto.max_hp, prototype_id=mob_id, home_room_id=room.id, game=game)
        instance.quests = proto.quests
        instance.can_be_companion = proto.can_be_companion
        instance.cooldowns = {} # Initialize for AI usage
        instance.active_class = None # Initialize for Engine compatibility
        instance.skills = getattr(proto, 'skills', []) # Copy skills
        instance.resources = {
            Tags.CONCENTRATION: instance.get_max_resource(Tags.CONCENTRATION),
            Tags.HEAT: 0,
            Tags.CHI: 0
        }
        
        # Apply deltas
        for k, v in deltas.items():
            if k != 'id':
                setattr(instance, k, v)
        
        instance.room = room
        room.monsters.append(instance)
        room.broadcast(f"A {instance.name} arrives.")
        # logger.info(f"Respawned {instance.name} in {room.id}")
        
        # EVENT: Mob Spawned
        event_engine.dispatch("mob_spawned", {'mob': instance, 'game': game})
        return instance
    return None

def notify_death(game, mob):
    """Called when a mob dies to schedule a respawn."""
    if not mob.home_room_id or not mob.prototype_id:
        return # Cannot respawn transient mobs
        
    # Schedule respawn (30-60 seconds = 15-30 ticks)
    delay = random.randint(15, 30)
    respawn_tick = game.tick_count + delay
    
    # We need to find the original static definition to respawn correctly
    # For simplicity, we'll just use the prototype ID
    game.world.pending_respawns.append({
        'tick': respawn_tick,
        'room_id': mob.home_room_id,
        'mob_data': mob.prototype_id
    })

def check_respawns(game):
    """Heartbeat task to manage mob respawns."""
    active_timers = []
    for task in game.world.pending_respawns:
        if game.tick_count >= task['tick']:
            room = game.world.rooms.get(task['room_id'])
            if room:
                spawn_mob(room, task['mob_data'], game)
            else:
                logger.debug(f"Skipping respawn for missing room {task['room_id']}")
        else:
            active_timers.append(task)
            
    game.world.pending_respawns = active_timers

def initialize_spawns(game):
    """
    Runs once at startup. 
    Checks all rooms. If a static mob is missing (and not in save file), spawn it.
    """
    logger.info("Initializing world population...")
    for room in game.world.rooms.values():
        if not hasattr(room, 'blueprint_monsters') or not room.blueprint_monsters:
            continue
            
        # Count active mobs in this room
        active_counts = {}
        for m in room.monsters:
            if m.prototype_id:
                active_counts[m.prototype_id] = active_counts.get(m.prototype_id, 0) + 1
            
        for mob_data in room.blueprint_monsters:
            mid = mob_data.get('id') if isinstance(mob_data, dict) else mob_data
            if active_counts.get(mid, 0) > 0:
                active_counts[mid] -= 1
            else:
                # Mob is missing from save (or fresh start), spawn it immediately
                spawn_mob(room, mob_data, game)