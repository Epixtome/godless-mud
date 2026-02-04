import logging

# Setup shared logger
logger = logging.getLogger("GodlessMUD")

# Import all classes to expose them at the package level
from .items import GameEntity, BaseItem, Item, Armor, Weapon, Consumable, Corpse
from .meta import Blessing, Quest, Class, Deity, Synergy, HelpEntry
from .world import Room, Door, Zone
from .entities import Monster, Player

__all__ = [
    "GameEntity", "BaseItem", "Item", "Armor", "Weapon", "Consumable", "Corpse",
    "Blessing", "Quest", "Class", "Deity", "Synergy", "HelpEntry",
    "Room", "Door", "Zone",
    "Monster", "Player"
]