import logging
import random
from models.items import Item, Armor, Weapon, Consumable, Currency, create_item_from_dict

logger = logging.getLogger("GodlessMUD")

def create_item(item_id, game=None):
    """
    Creates an item instance from its prototype ID.
    Searches across all item categories in world.items.
    """
    # 1. Access the global items registry if game is provided
    # Fallback: Many callers won't have the game object yet, 
    # so we might need a more global registry or a specialized loader.
    
    # In Godless, the 'game' object's world has the items.
    if not game:
        # Resolve global game if possible, or use a cached global world
        from godless_mud import global_game
        game = global_game

    if not game or not hasattr(game, 'world'):
        logger.error(f"Cannot create item {item_id}: Game/World not available.")
        return None

    proto = game.world.items.get(item_id)
    if not proto:
        # Try searching by matching case-insensitive name if ID fails
        for p_id, p_obj in game.world.items.items():
            if p_id and item_id and p_id.lower() == item_id.lower():
                proto = p_obj
                break
        
    if not proto:
        logger.warning(f"Item prototype {item_id} not found in world registry.")
        return None

    # Clone the prototype
    return proto.clone()

def create_currency(amount, coin_type="gold"):
    """Shorthand to create currency items."""
    return Currency(amount, coin_type)
