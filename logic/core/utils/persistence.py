"""
logic/core/utils/persistence.py
Domain: Serialization, Save/Load, and Entity Hydration.
Ensures data parity for JSON player saves.
"""
import os
import json
import logging
from typing import TYPE_CHECKING
from models.items import Item, Armor, Weapon, Consumable

if TYPE_CHECKING:
    from models.entities.player import Player

logger = logging.getLogger("GodlessMUD")

def to_dict(player: 'Player') -> dict:
    """Serializes player state to a dictionary for JSON saving."""
    return {
        "name": player.name,
        "room_id": player.room.id if player.room else None,
        "hp": player.hp,
        "identity_tags": player.identity_tags,
        "known_blessings": player.known_blessings,
        "equipped_blessings": player.equipped_blessings,
        "blessing_charges": player.blessing_charges,
        "blessing_xp": player.blessing_xp,
        "resources": player.resources,
        "active_class": player._active_class,
        "unlocked_classes": player.unlocked_classes,
        "favor": player.favor,
        "gold": player.gold,
        "aliases": player.aliases,
        "cooldowns": player.cooldowns,
        "inventory": [item.to_dict() for item in player.inventory],
        "is_resting": player.is_resting,
        "rest_until": player.rest_until,
        "active_quests": player.active_quests,
        "completed_quests": player.completed_quests,
        "status_effects": player.status_effects,
        "password": player.password,
        "is_admin": player.is_admin,
        "is_building": player.is_building,
        "equipped_armor": player.equipped_armor.to_dict() if player.equipped_armor else None,
        "equipped_weapon": player.equipped_weapon.to_dict() if player.equipped_weapon else None,
        "equipped_offhand": player.equipped_offhand.to_dict() if player.equipped_offhand else None,
        "friendship": player.friendship,
        "visited_rooms": list(player.visited_rooms),
        "reputation": player.reputation,
        "ext_state": player.ext_state,
        "admin_vision": player.admin_vision,
        "active_kit": player.active_kit,
        "last_hit_tick": player.last_hit_tick,
        "last_action": player.last_action
    }

def load_data(player, data):
    """Hydrates player state from a dictionary."""
    player.hp = data.get('hp', player.hp)
    player.gold = data.get('gold', 0)
    
    player.identity_tags = data.get('identity_tags', player.identity_tags)
    player.known_blessings = data.get('known_blessings', [])
    player.equipped_blessings = data.get('equipped_blessings', [])
    
    if 'blessing_charges' in data:
        player.blessing_charges.update(data['blessing_charges'])
        
    if 'blessing_xp' in data:
        player.blessing_xp.update(data['blessing_xp'])
        
    if 'resources' in data:
        player.resources.update(data['resources'])
            
    favor_data = data.get('favor', {})
    if isinstance(favor_data, dict):
        player.favor.update(favor_data)
        
    player._active_class = data.get('active_class')
    player.unlocked_classes = data.get('unlocked_classes', [])
    if 'aliases' in data:
        player.aliases.update(data['aliases'])
    
    if 'cooldowns' in data:
        player.cooldowns.update(data['cooldowns'])
        
    player.is_resting = data.get('is_resting', False)
    player.rest_until = data.get('rest_until', 0)

    player.active_quests = data.get('active_quests', {})
    player.completed_quests = data.get('completed_quests', [])

    if 'status_effects' in data:
        player.status_effects.update(data['status_effects'])
    
    player.password = data.get('password')
    player.is_admin = data.get('is_admin', False)
    player.is_building = data.get('is_building', False)
    
    if 'friendship' in data:
        player.friendship.update(data['friendship'])
        
    player.visited_rooms = set(data.get('visited_rooms', []))
    player.reputation = data.get('reputation', 0)
    player.ext_state = data.get('ext_state', {})
    player.admin_vision = data.get('admin_vision', False)
    player.last_hit_tick = data.get('last_hit_tick', 0)
    player.last_action = data.get('last_action', "none")
    player.active_kit = data.get('active_kit', {})
    
    player.trigger_module_inits()
    
    # Reconstruct Inventory
    player.inventory = []
    for item_data in data.get('inventory', []):
        it_type = item_data.get('type')
        if it_type == 'armor':
            player.inventory.append(Armor.from_dict(item_data))
        elif it_type == 'weapon':
            player.inventory.append(Weapon.from_dict(item_data))
        elif it_type == 'consumable':
            player.inventory.append(Consumable.from_dict(item_data))
        elif it_type == 'item':
            player.inventory.append(Item.from_dict(item_data))
    
    if data.get('equipped_armor'):
        player.equipped_armor = Armor.from_dict(data['equipped_armor'])
    if data.get('equipped_weapon'):
        player.equipped_weapon = Weapon.from_dict(data['equipped_weapon'])
    if data.get('equipped_offhand'):
        player.equipped_offhand = Armor.from_dict(data['equipped_offhand'])

    player.reset_resources()

def save(player):
    """Saves the player data to disk."""
    try:
        os.makedirs(os.path.join("data", "saves"), exist_ok=True)
        filename = os.path.join("data", "saves", f"{player.name.lower()}.json")
        with open(filename, 'w') as f:
            json.dump(to_dict(player), f, indent=4)
        logger.info(f"Saved {player.name}")
    except Exception as e:
        logger.error(f"Failed to save {player.name}: {e}")

def load_kit(player, kit_name):
    """Loads a kit from data/kits.json and applies it."""
    try:
        with open(os.path.join("data", "kits.json"), "r") as f:
            kits = json.load(f)
        
        if kit_name in kits:
            player.active_kit = kits[kit_name]
            # Identity Mapping
            from logic.constants import Tags
            if kit_name == 'barbarian':
                player.identity_tags = [Tags.MARTIAL]
            elif kit_name == 'knight':
                player.identity_tags = [Tags.MARTIAL, 'light']
            elif kit_name == 'mage':
                player.identity_tags = [Tags.MAGIC, 'arcane']
            else:
                player.identity_tags = ['adventurer']
            
            player.trigger_module_inits()
            return True
    except Exception as e:
        logger.error(f"Failed to load kit {kit_name}: {e}")
    return False

def trigger_module_inits(player):
    """
    Dynamically initializes state for all active modules in logic/modules/.
    Supports both generic 'initialize' and naming-conv 'initialize_[name]' 
    at either the state submodule or package level.
    """
    import importlib
    import pkgutil
    import logic.modules

    # Iterate through all sub-packages in logic.modules
    path = logic.modules.__path__
    for loader, module_name, is_pkg in pkgutil.iter_modules(path):
        if not is_pkg or module_name == 'common':
            continue
            
        try:
            # 1. Try to initialize via state submodule (GCA Standard)
            state_path = f"logic.modules.{module_name}.state"
            try:
                state_mod = importlib.import_module(state_path)
                init_func = getattr(state_mod, 'initialize', None)
                if not init_func:
                    init_func = getattr(state_mod, f"initialize_{module_name}", None)
                
                if init_func:
                    init_func(player)
                    continue # Successfully initialized via state
            except ImportError:
                pass # No state.py, falling back to package-level check

            # 2. Fallback to package-level initialization
            module_path = f"logic.modules.{module_name}"
            class_mod = importlib.import_module(module_path)
            init_func = getattr(class_mod, 'initialize', None)
            if not init_func:
                init_func = getattr(class_mod, f"initialize_{module_name}", None)
            
            if init_func:
                init_func(player)

        except Exception as e:
            logger.error(f"Failed to auto-discover init for {module_name}: {e}")
