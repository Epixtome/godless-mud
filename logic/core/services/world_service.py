"""
logic/core/services/world_service.py
Service layer for world entity management (Spawning, Purging, Searching).
Enforces Pillar 6 (Anemic Model delegation).
"""
import logging
from models import Monster, Item
from logic.core import event_engine

logger = logging.getLogger("GodlessMUD")

def spawn_monster(game, proto_id, room, count=1):
    """
    Safely spawns one or more monsters into a room.
    Handles cloning, inventory loading, and room registration.
    """
    proto = game.world.monsters.get(proto_id)
    if not proto:
        logger.warning(f"WorldService: Attempted to spawn non-existent prototype {proto_id}")
        return None

    spawned = []
    for _ in range(count):
        # 1. Clone/Instantiate
        new_mob = Monster(
            proto.name, proto.description, getattr(proto, 'max_hp', 100), proto.damage, 
            tags=getattr(proto, 'tags', []), max_hp=getattr(proto, 'max_hp', 100), 
            prototype_id=proto_id
        )
        new_mob.game = game
        new_mob.room = room
        
        # 2. Add Loadout
        loadout = getattr(proto, 'loadout', [])
        for item_id in loadout:
            item_proto = game.world.items.get(item_id)
            if item_proto:
                item = item_proto.clone()
                if hasattr(item, 'type') and item.type != 'weapon' and not new_mob.equipped_offhand:
                    new_mob.equipped_offhand = item
                else:
                    new_mob.inventory.append(item)

        # 3. Spatial Registration
        room.monsters.append(new_mob)
        spawned.append(new_mob)
        
        # 4. Event Hook
        event_engine.dispatch("mob_spawned", {'mob': new_mob})

    return spawned

def spawn_item(game, proto_id, target, count=1):
    """
    Spawns an item into a target (Player inventory or Room).
    """
    proto = game.world.items.get(proto_id)
    if not proto:
        return None

    spawned = []
    for _ in range(count):
        item = proto.clone()
        
        if hasattr(target, 'inventory'): # Entity (Player/Monster)
            target.inventory.append(item)
        elif hasattr(target, 'items'): # Room
            target.items.append(item)
            
        # Handle Decayregistration if system available
        if hasattr(item, 'flags') and "decay" in item.flags:
            from logic import systems
            systems.register_decay(game, item, getattr(target, 'room', target))

        spawned.append(item)
    
    return spawned

def purge_room(room, purge_type="all"):
    """Safely clears a room of entities."""
    if purge_type in ['all', 'mobs']:
        room.monsters.clear()
    if purge_type in ['all', 'items']:
        room.items.clear()
    return True
