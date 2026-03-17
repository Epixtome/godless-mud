"""
logic/core/services/world_service.py
Service layer for world entity management (Spawning, Purging, Searching).
Enforces Pillar 6 (Anemic Model delegation).
"""
import logging
from models import Monster, Item
from logic.core import event_engine

logger = logging.getLogger("GodlessMUD")

def register_dynamic_prototype(game, entity):
    """
    Registers a dynamically generated entity as a valid world prototype.
    Allows it to be referenced by ID for spawning and zone persistence.
    """
    if not entity or not hasattr(entity, 'prototype_id'):
        return None
    
    p_id = entity.prototype_id
    if p_id in game.world.monsters or p_id in game.world.items:
        # Already exists, just return the ID
        return p_id

    if isinstance(entity, Monster):
        game.world.monsters[p_id] = entity
    elif isinstance(entity, Item):
        game.world.items[p_id] = entity
    else:
        return None
        
    logger.info(f"Registered dynamic prototype: {p_id}")
    return p_id

def spawn_monster(game, proto_id, room, count=1):
    """
    Safely spawns one or more monsters into a room.
    Handles cloning, inventory loading, and room registration.
    """
    proto = game.world.monsters.get(proto_id)
    if not proto:
        logger.warning(f"WorldService: Attempted to spawn non-existent prototype {proto_id}")
        return None

    from logic.core.factory import get_monster
    spawned = []
    for _ in range(count):
        # 1. Instantiate via Factory to ensure Prototype Consistency
        new_mob = get_monster(proto_id, game.world)
        if not new_mob: continue
        
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
        
        # 4. Active Room Registry
        game.world.register_room(room)
        
        # 5. Event Hook
        event_engine.dispatch("mob_spawned", {'mob': new_mob})

    return spawned

def spawn_item(game, proto_id, target, count=1):
    """
    Spawns an item into a target (Player inventory or Room).
    """
    proto = game.world.items.get(proto_id)
    if not proto:
        return None

    from logic.core.factory import get_item
    spawned = []
    for _ in range(count):
        # Use Dynamic Factory to build a validated item instance
        item = get_item(proto_id, game.world)
        if not item: continue
        
        if hasattr(target, 'inventory'): # Entity (Player/Monster)
            target.inventory.append(item)
        elif hasattr(target, 'items'): # Room
            target.items.append(item)
            
        # Handle Decay registration if system available
        if hasattr(item, 'flags') and "decay" in item.flags:
            from logic import systems
            systems.register_decay(game, item, getattr(target, 'room', target))

        spawned.append(item)
    
    return spawned

def move_entity(entity, target_room):
    """
    Service: Unified movement for Players and Monsters.
    Maintains the Active Room Registry on every transition.
    """
    if not entity or not target_room:
        return False

    old_room = getattr(entity, 'room', None)
    world = entity.game.world if getattr(entity, 'game', None) else None

    if old_room:
        if entity in old_room.players:
            old_room.players.remove(entity)
        if entity in old_room.monsters:
            old_room.monsters.remove(entity)
        # Deregister old room if it's now empty
        if world:
            world.deregister_room(old_room)

    entity.room = target_room
    if getattr(entity, 'is_player', False):
        if entity not in target_room.players:
            target_room.players.append(entity)
    else:
        if entity not in target_room.monsters:
            target_room.monsters.append(entity)

    # Register the destination as active
    if world:
        world.register_room(target_room)
    
    event_engine.dispatch("on_enter_room", {'entity': entity, 'room': target_room})
    return True

def purge_room(room, purge_type="all"):
    """Safely clears a room of entities."""
    if purge_type in ['all', 'mobs']:
        room.monsters.clear()
    if purge_type in ['all', 'items']:
        room.items.clear()
    
    # Surgical Purge (Targeted)
    if purge_type not in ['all', 'mobs', 'items']:
        from logic.core import search
        target = search.search_list(room.monsters, purge_type) or search.search_list(room.items, purge_type)
        if target:
            if target in room.monsters: room.monsters.remove(target)
            if target in room.items: room.items.remove(target)
            return True
        return False
        
    return True
