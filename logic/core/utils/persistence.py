"""
logic/core/utils/persistence.py
Domain: Serialization, Save/Load, and Entity Hydration.
Ensures data parity for JSON player saves.
V5.3: Integrated "Archive Health" and Kit Migration Protocols.
"""
import os
import json
import logging
from typing import TYPE_CHECKING
from models.items import Item, Armor, Weapon, Consumable

if TYPE_CHECKING:
    from models.entities.player import Player

logger = logging.getLogger("GodlessMUD")

def item_from_data(item_data, game=None):
    """Reconstructs an item from a dictionary or string ID (Prototype)."""
    if isinstance(item_data, str):
        # Resolve from world prototypes (Department of Manufacturing)
        if game and item_data in game.world.items:
            prototype = game.world.items[item_data]
            return prototype.clone() if hasattr(prototype, 'clone') else prototype
        return None

    if not isinstance(item_data, dict):
        return None

    it_type = item_data.get('type', 'item')
    if it_type == 'armor':
        return Armor.from_dict(item_data)
    elif it_type == 'weapon':
        return Weapon.from_dict(item_data)
    elif it_type == 'consumable':
        return Consumable.from_dict(item_data)
    
    return Item.from_dict(item_data)

def to_dict(player: 'Player') -> dict:
    """Serializes player state to a dictionary for JSON saving."""
    return {
        "name": player.name,
        "room_id": player.room.id if player.room else None,
        "hp": player.hp,
        "identity_tags": list(set(player.identity_tags)), # Deduplicate
        "known_blessings": list(set(player.known_blessings)),
        "equipped_blessings": list(set(player.equipped_blessings)),
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
        "equipped_armor": player.equipped_armor.to_dict() if getattr(player, 'equipped_armor', None) else None,
        "equipped_weapon": player.equipped_weapon.to_dict() if getattr(player, 'equipped_weapon', None) else None,
        "equipped_offhand": player.equipped_offhand.to_dict() if getattr(player, 'equipped_offhand', None) else None,
        "equipped_head": player.equipped_head.to_dict() if getattr(player, 'equipped_head', None) else None,
        "equipped_neck": player.equipped_neck.to_dict() if getattr(player, 'equipped_neck', None) else None,
        "equipped_shoulders": player.equipped_shoulders.to_dict() if getattr(player, 'equipped_shoulders', None) else None,
        "equipped_arms": player.equipped_arms.to_dict() if getattr(player, 'equipped_arms', None) else None,
        "equipped_hands": player.equipped_hands.to_dict() if getattr(player, 'equipped_hands', None) else None,
        "equipped_legs": player.equipped_legs.to_dict() if getattr(player, 'equipped_legs', None) else None,
        "equipped_feet": player.equipped_feet.to_dict() if getattr(player, 'equipped_feet', None) else None,
        "equipped_finger_l": player.equipped_finger_l.to_dict() if getattr(player, 'equipped_finger_l', None) else None,
        "equipped_finger_r": player.equipped_finger_r.to_dict() if getattr(player, 'equipped_finger_r', None) else None,
        "equipped_floating": player.equipped_floating.to_dict() if getattr(player, 'equipped_floating', None) else None,
        "equipped_mount": player.equipped_mount.to_dict() if getattr(player, 'equipped_mount', None) else None,
        "friendship": player.friendship,
        "visited_rooms": list(player.visited_rooms),
        "discovered_rooms": list(player.discovered_rooms),
        "reputation": player.reputation,
        "kingdom": player.kingdom,
        "ext_state": player.ext_state,
        "admin_vision": player.admin_vision,
        "active_kit": player.active_kit,
        "kit_version": getattr(player, 'kit_version', 0),
        "last_hit_tick": player.last_hit_tick,
        "last_action": player.last_action
    }

def load_data(player, data):
    """Hydrates player state from a dictionary with Migration support."""
    player.hp = data.get('hp', player.hp)
    player.gold = data.get('gold', 0)
    
    # Pillar 1: Clean Identity
    player.identity_tags = list(set(data.get('identity_tags', player.identity_tags)))
    player.known_blessings = list(set(data.get('known_blessings', [])))
    player.equipped_blessings = list(set(data.get('equipped_blessings', [])))
    
    player.blessing_charges.update(data.get('blessing_charges', {}))
    player.blessing_xp.update(data.get('blessing_xp', {}))
    player.resources.update(data.get('resources', {}))
    player.favor.update(data.get('favor', {}))
        
    player._active_class = data.get('active_class')
    player.unlocked_classes = data.get('unlocked_classes', [])
    player.aliases.update(data.get('aliases', {}))
    # [V5.3 Standard] Sanitize Absolute Tick References (Prevention of Snapshot Poisoning)
    # Since tick_count resets to 0 on server restarts, any absolute ticks in saves
    # must be cleared or they will cause infinite locks (Cooldowns) or permanent buffs.
    player.cooldowns = {}
    player.status_effects = {}
    player.last_hit_tick = 0
    player.last_action = "none"
    
    # We do NOT update from data for these keys to ensure clean-slate on connect.
    # player.cooldowns.update(data.get('cooldowns', {})) # DEPRECATED
        
    player.is_resting = data.get('is_resting', False)
    player.rest_until = data.get('rest_until', 0)
    player.active_quests = data.get('active_quests', {})
    player.completed_quests = data.get('completed_quests', [])
    # player.status_effects.update(data.get('status_effects', {})) # DEPRECATED
    
    player.password = data.get('password')
    player.is_admin = data.get('is_admin', False)
    player.is_building = data.get('is_building', False)
    player.friendship.update(data.get('friendship', {}))
    player.visited_rooms = data.get('visited_rooms', [])
    player.discovered_rooms = data.get('discovered_rooms', [])
    player.reputation = data.get('reputation', 0)
    player.kingdom = data.get('kingdom', 'instinct')
    player.ext_state = data.get('ext_state', {})
    player.admin_vision = data.get('admin_vision', False)
    # player.last_hit_tick = data.get('last_hit_tick', 0) # DEPRECATED
    # player.last_action = data.get('last_action', "none") # DEPRECATED
    player.active_kit = data.get('active_kit', {})
    player.kit_version = data.get('kit_version', 0)

    # Pillar 2: The Archive Health Check (Kit Synchronization)
    if player._active_class:
        # If the kit version is old or missing, force a migration
        # This prevents "Snapshot Poisoning" where the player is stuck with old skills
        load_kit(player, player._active_class)
    
    player.trigger_module_inits()
    
    # Reconstruct Inventory (with game world resolution)
    player.inventory = []
    for item_data in data.get('inventory', []):
        item = item_from_data(item_data, game=player.game)
        if item:
            player.inventory.append(item)
    
    if data.get('equipped_armor'):
        player.equipped_armor = item_from_data(data['equipped_armor'], game=player.game)
    if data.get('equipped_weapon'):
        player.equipped_weapon = item_from_data(data['equipped_weapon'], game=player.game)
    if data.get('equipped_offhand'):
        player.equipped_offhand = item_from_data(data['equipped_offhand'], game=player.game)
    if data.get('equipped_head'):
        player.equipped_head = item_from_data(data['equipped_head'], game=player.game)
    if data.get('equipped_neck'):
        player.equipped_neck = item_from_data(data['equipped_neck'], game=player.game)
    if data.get('equipped_shoulders'):
        player.equipped_shoulders = item_from_data(data['equipped_shoulders'], game=player.game)
    if data.get('equipped_arms'):
        player.equipped_arms = item_from_data(data['equipped_arms'], game=player.game)
    if data.get('equipped_hands'):
        player.equipped_hands = item_from_data(data['equipped_hands'], game=player.game)
    if data.get('equipped_legs'):
        player.equipped_legs = item_from_data(data['equipped_legs'], game=player.game)
    if data.get('equipped_feet'):
        player.equipped_feet = item_from_data(data['equipped_feet'], game=player.game)
    if data.get('equipped_finger_l'):
        player.equipped_finger_l = item_from_data(data['equipped_finger_l'], game=player.game)
    if data.get('equipped_finger_r'):
        player.equipped_finger_r = item_from_data(data['equipped_finger_r'], game=player.game)
    if data.get('equipped_floating'):
        player.equipped_floating = item_from_data(data['equipped_floating'], game=player.game)
    if data.get('equipped_mount'):
        player.equipped_mount = item_from_data(data['equipped_mount'], game=player.game)

    player.reset_resources()

def save(player):
    """Saves the player data to disk (Department of Archives)."""
    try:
        os.makedirs(os.path.join("data", "saves"), exist_ok=True)
        filename = os.path.join("data", "saves", f"{player.name.lower()}.json")
        with open(filename, 'w') as f:
            json.dump(to_dict(player), f, indent=4)
        logger.info(f"Saved Archive: {player.name}")
    except Exception as e:
        logger.error(f"Failed to save {player.name}: {e}")

def load_kit(player, kit_name):
    """Loads a kit from data/kits.json and applies it with V5.3 migration support."""
    try:
        with open(os.path.join("data", "kits.json"), "r") as f:
            kits = json.load(f)
        
        if kit_name in kits:
            kit_data = kits[kit_name]
            current_version = kit_data.get('version', 1)
            player_version = getattr(player, 'kit_version', 0)

            # [V5.3 Standard] Force Migration if versions differ
            if player_version < current_version:
                migrate_kit(player, kit_data)
            
            # Update live kit data in player object
            kit_data['id'] = kit_name
            player.active_kit = kit_data
            player.kit_version = current_version
            
            # Ensure identity tags are synced
            kit_tags = kit_data.get('identity_tags', [])
            for tag in kit_tags:
                if tag not in player.identity_tags:
                    player.identity_tags.append(tag)
            
            return True
    except Exception as e:
        logger.error(f"Failed to load kit {kit_name}: {e}")
    return False

def migrate_kit(player, kit_data):
    """Surgically reconciles player blessings with the global Kit Blueprint."""
    new_blessings = kit_data.get('blessings', [])
    old_kit_blessings = player.active_kit.get('blessings', []) if player.active_kit else []
    
    # 1. Removal: Take away any "Old Kit" blessings that the player shouldn't have anymore
    # We compare what was in the old kit vs the new kit
    to_remove = set(old_kit_blessings) - set(new_blessings)
    for b_id in to_remove:
        if b_id in player.known_blessings:
            player.known_blessings.remove(b_id)
        if b_id in player.equipped_blessings:
            player.equipped_blessings.remove(b_id)
            
    # 2. Injection: Add the new Blueprint blessings
    for b_id in new_blessings:
        if b_id not in player.known_blessings:
            player.known_blessings.append(b_id)
        if b_id not in player.equipped_blessings:
            player.equipped_blessings.append(b_id)
            
    logger.info(f"[MIGRATION] Synchronized {player.name} to {kit_data.get('name')} v{kit_data.get('version')}")

def trigger_module_inits(player):
    """
    Initializes state for the active class module and common modules.
    Replaces the legacy 'Initialize All' approach.
    """
    import importlib
    
    # We always load 'common', plus the active class
    active_class = getattr(player, 'active_class', None)
    target_modules = ['common']
    if active_class:
        target_modules.append(active_class.lower())

    for module_name in target_modules:
        try:
            # GCA Standard: logic.modules.[classname].state
            state_path = f"logic.modules.{module_name}.state"
            try:
                state_mod = importlib.import_module(state_path)
                
                # Check for multiple init patterns (initialize or initialize_name)
                init_func = getattr(state_mod, 'initialize', None)
                if not init_func:
                    init_func = getattr(state_mod, f"initialize_{module_name}", None)
                
                if init_func:
                    init_func(player)
            except ImportError:
                # No state.py found for this module, which is fine for simple modules
                pass 

        except Exception as e:
            logger.error(f"Failed to initialize department logic for {module_name}: {e}")
