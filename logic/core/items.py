"""
logic/core/items.py
Centralized Item Facade for Godless.
Pillar 1: Clean Border Protocol. Standardizes transfers and equipment.
"""
import logging
from logic.engines.resonance_engine import ResonanceAuditor
from logic.core import resources, effects
from utilities import telemetry
from models.items import Currency

logger = logging.getLogger("GodlessMUD")

def transfer_item(item, source, destination):
    """
    Moves an item from a source (Entity or List) to a destination.
    The single source of truth for avoiding item duplication.
    """
    if not item or source is None or destination is None:
        return False

    # Resolve lists
    s_list = source.inventory if hasattr(source, 'inventory') else source
    d_list = destination.inventory if hasattr(destination, 'inventory') else destination

    if not isinstance(s_list, list) or not isinstance(d_list, list):
        logger.error(f"Transfer failed: Source or Destination has no inventory list. {type(s_list)} -> {type(d_list)}")
        return False

    if item not in s_list:
        logger.warning(f"Transfer aborted: Item '{item.name}' not in source list.")
        return False

    # Perform Move
    s_list.remove(item)
    d_list.append(item)

    # Register Dirty State for Persistence
    if hasattr(source, 'dirty'): source.dirty = True
    if hasattr(destination, 'dirty'): destination.dirty = True

    # Pacing and Weight Recalculation
    for entity in [source, destination]:
        if hasattr(entity, 'identity_tags'): # Player/Monster identifying check
            resources.calculate_total_weight(entity)
            ResonanceAuditor.calculate_resonance(entity)
            if hasattr(entity, 'move_tokens'): # Pacing update for players
                resources.update_max_hp(entity)
    
    return True

def give_item(player, item, source_container=None, silent=False):
    """Adds an item to a player's inventory with validation and messages."""
    if isinstance(item, Currency):
        player.gold += item.amount
        if not silent:
            player.send_line(f"You pick up {item.name}. ({item.amount} added to gold)")
        # Currencies are consumed upon pickup, we must remove from source if it exists
        if source_container:
            s_list = source_container.inventory if hasattr(source_container, 'inventory') else source_container
            if s_list and isinstance(s_list, list) and item in s_list:
                s_list.remove(item)
        return True

    # Inventory Capacity Check
    if len(player.inventory) >= player.inventory_limit:
        if not silent: player.send_line("Your inventory is full.")
        return False

    if transfer_item(item, source_container, player):
        if not silent:
            if source_container and hasattr(source_container, 'name'):
                player.send_line(f"You get {item.name} from {source_container.name}.")
            else:
                player.send_line(f"You pick up {item.name}.")
        return True
    return False

def drop_item(player, item, silent=False):
    """Drops an item from player's inventory to the room."""
    if not player or not player.room: return False
    
    if transfer_item(item, player, player.room):
        if not silent:
            player.send_line(f"You drop {item.name}.")
            player.room.broadcast(f"{player.name} drops {item.name}.", exclude_player=player)
        return True
    return False

def equip_item(player, item, silent=False):
    """
    Facade for wearing/wielding gear.
    Handles swapping, inventory limits, and stat updates.
    """
    target_slot = getattr(item, 'slot', None)
    if not target_slot:
        if not silent: player.send_line("This item cannot be equipped.")
        return False

    target_slot = target_slot.lower().replace(" ", "_")
    slot_attr_map = {
        "head": "equipped_head", "neck": "equipped_neck",
        "chest": "equipped_armor", "body": "equipped_armor",
        "arms": "equipped_arms", "hands": "equipped_hands",
        "legs": "equipped_legs", "feet": "equipped_feet",
        "main_hand": "equipped_weapon", "wield": "equipped_weapon",
        "off_hand": "equipped_offhand", "shield": "equipped_offhand",
        "floating": "equipped_floating", "mount": "equipped_mount"
    }
    
    player_attr = slot_attr_map.get(target_slot)
    if not player_attr:
        if not silent: player.send_line(f"Invalid slot: {target_slot}")
        return False

    # Check for Swap
    current_item = getattr(player, player_attr, None)
    if current_item:
        if len(player.inventory) >= player.inventory_limit:
            if not silent: player.send_line(f"Inventory full, cannot swap {target_slot}.")
            return False
        # Move current to inventory
        setattr(player, player_attr, None)
        player.inventory.append(current_item)
        if not silent: player.send_line(f"You unequip {current_item.name}.")

    # Special 2H Logic
    if player_attr == "equipped_weapon" and getattr(item, 'hands', 1) == 2:
        offhand = getattr(player, 'equipped_offhand', None)
        if offhand:
            if len(player.inventory) >= player.inventory_limit:
                 if not silent: player.send_line("Inventory full, cannot unequip offhand for 2H weapon.")
                 return False
            player.equipped_offhand = None
            player.inventory.append(offhand)
            if not silent: player.send_line(f"You unequip {offhand.name} to wield {item.name}.")

    # Perform Equipment
    if item in player.inventory:
        player.inventory.remove(item)
    setattr(player, player_attr, item)
    
    # Recalculate
    ResonanceAuditor.calculate_resonance(player)
    resources.calculate_total_weight(player)
    resources.update_max_hp(player)
    telemetry.log_stat_snapshot(player, player.current_tags)
    
    if not silent:
        verb = "wield" if target_slot in ["main_hand", "wield"] else "wear"
        player.send_line(f"You {verb} {item.name}.")
    return True

def unequip_item(player, item, silent=False):
    """Removes an item from a slot and places it in inventory."""
    if len(player.inventory) >= player.inventory_limit:
        if not silent: player.send_line("Inventory full, cannot remove item.")
        return False

    # Find the slot
    found_attr = None
    known_attrs = [
        "equipped_weapon", "equipped_offhand", "equipped_armor",
        "equipped_head", "equipped_neck", "equipped_shoulders",
        "equipped_arms", "equipped_hands", "equipped_finger_l",
        "equipped_finger_r", "equipped_legs", "equipped_feet",
        "equipped_floating", "equipped_mount"
    ]
    
    for attr in known_attrs:
        if getattr(player, attr, None) == item:
            found_attr = attr
            break
            
    if not found_attr:
        return False

    setattr(player, found_attr, None)
    player.inventory.append(item)
    
    ResonanceAuditor.calculate_resonance(player)
    resources.calculate_total_weight(player)
    resources.update_max_hp(player)
    
    if not silent:
        player.send_line(f"You remove {item.name}.")
    return True
