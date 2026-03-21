
"""
logic/core/factory.py
The Unified Entity Factory. Implements the Blueprint + Delta pattern.
Ensures that all objects (Mobs, Items) inherit required properties from their prototypes.
"""
import logging
from models.items import create_item_from_dict
from logic.core.world import World

logger = logging.getLogger("GodlessMUD")

def get_item(prototype_id, world=None):
    """
    Creates a new item instance from a prototype.
    """
    if world is None:
        from logic.core.world import World
        world = World() # Fallback for singleton access

    proto_data = world.items.get(prototype_id)
    if not proto_data:
        # Check if prototype is already a model object
        if hasattr(prototype_id, 'clone'):
            return prototype_id.clone()
        logger.error(f"Factory Error: Item Prototype '{prototype_id}' not found.")
        return None

    # [V7.2] Robust Object Handling: If proto_data is already an item object, clone it.
    if hasattr(proto_data, 'clone'):
        return proto_data.clone()

    # Create from dict handles the class selection (Weapon, Armor, etc)
    item = create_item_from_dict(proto_data)
    item.prototype_id = prototype_id
    return item

def get_monster(prototype_id, world):
    """
    Creates a new monster instance from a prototype.
    """
    proto_data = world.monsters.get(prototype_id)
    if not proto_data:
        # Check if the prototype_id itself is a model object being passed in
        if hasattr(prototype_id, 'name'):
            proto_data = prototype_id
        else:
            logger.error(f"Factory Error: Monster Prototype '{prototype_id}' not found.")
            return None

    # [V5.3 Fix] Handle proto_data being either a dict or a Monster object
    if hasattr(proto_data, 'to_dict'):
        data = proto_data.to_dict()
    elif isinstance(proto_data, dict):
        data = proto_data
    else:
        # Fallback for weird objects or classes
        data = vars(proto_data)

    from models.entities import Monster
    # Ensure monster inherits all requirements from prototype
    mob = Monster(
        name=data.get('name', "Unknown"),
        description=data.get('description', "A mysterious entity."),
        hp=data.get('hp', 20),
        damage=data.get('damage', 1),
        tags=data.get('tags', []),
        max_hp=data.get('max_hp', data.get('hp', 20)),
        prototype_id=prototype_id,
        game=getattr(world, 'game', None)
    )
    
    # Apply extra proto fields (shouts, loot_table, etc)
    for k, v in data.items():
        if k not in ['name', 'description', 'hp', 'damage', 'tags', 'max_hp', 'id']:
            if not hasattr(mob, k) or getattr(mob, k) is None:
                setattr(mob, k, v)
            
    return mob

def get_structure(prototype_id, world):
    """
    [V6.5] Creates a new structure instance from a prototype.
    Structures share the monster prototype database but use the Structure model.
    """
    from models.entities import Structure
    proto_data = world.monsters.get(prototype_id)
    if not proto_data:
        logger.error(f"Factory Error: Structure Prototype '{prototype_id}' not found.")
        return None

    # Handle standard data merging
    data = proto_data.to_dict() if hasattr(proto_data, 'to_dict') else proto_data
    
    struct = Structure(
        name=data.get('name', "Unknown Structure"),
        description=data.get('description', "A fixed mechanical object."),
        hp=data.get('hp', 100),
        damage=data.get('damage', 0),
        tags=data.get('tags', ["structure"]),
        prototype_id=prototype_id,
        game=getattr(world, 'game', None)
    )
    
    # Default stationary logic if not in prototype
    struct.is_stationary = True
    
    # Generic attribute back-fill
    for k, v in data.items():
        if k not in ['name', 'description', 'hp', 'damage', 'tags', 'id']:
            setattr(struct, k, v)
            
    return struct

def instantiate_from_state(data, world):
    """
    Recreates an entity from saved live state delta.
    Ensures that missing fields are back-filled from the prototype.
    """
    p_id = data.get('prototype_id')
    e_type = data.get('type')

    if e_type in ['weapon', 'armor', 'item', 'consumable', 'currency']:
        # 1. Start with the Prototype 'Bin'
        proto = world.items.get(p_id) if p_id else {}
        if not proto and p_id:
            logger.warning(f"Instantiate Error: Item Proto '{p_id}' missing.")
            
        # If proto is an object, convert to dict for merging
        if hasattr(proto, 'to_dict'): proto = proto.to_dict()
            
        # 2. Layer the Delta (Saved state) on top of the Prototype
        merged_data = {**proto, **data}
        return create_item_from_dict(merged_data)
        
    elif e_type == 'monster':
        return get_monster(p_id, world) if p_id else None
        
    elif e_type == 'structure':
        return get_structure(p_id, world) if p_id else None

    return None
