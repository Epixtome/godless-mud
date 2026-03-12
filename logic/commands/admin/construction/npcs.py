import logic.handlers.command_manager as command_manager
from utilities.colors import Colors
from logic.core.utils import persistence

@command_manager.register("@makeshopkeeper", admin=True)
def make_shopkeeper(player, args):
    """
    Turns a spawned NPC into a shopkeeper.
    Usage: @makeshopkeeper <name>
    """
    if not args:
        player.send_line("Usage: @makeshopkeeper <npc_name>")
        return

    target = None
    for mob in player.room.monsters:
        if args.lower() in mob.name.lower():
            target = mob
            break

    if not target:
        player.send_line(f"NPC '{args}' not found in room.")
        return

    target.is_shopkeeper = True
    player.send_line(f"{Colors.GREEN}{target.name} is now a shopkeeper!{Colors.RESET}")
    player.room.dirty = True

@command_manager.register("@persist_room", admin=True)
def persist_room_mobs(player, args):
    """
    Saves all currently active mobs in the room into the room's blueprint.
    This makes them 'static' and persistent across restarts.
    Usage: @persist_room
    """
    room = player.room
    
    # Convert all active monsters to dicts and store in blueprint
    room.blueprint_monsters = []
    for mob in room.monsters:
        # We save the full dict so deltas (names, inventories, levels) are kept
        mob_data = mob.to_dict()
        # Ensure we have the prototype_id for respawn logic
        mob_data['id'] = mob.prototype_id 
        room.blueprint_monsters.append(mob_data)
        
    room.dirty = True
    player.send_line(f"{Colors.GREEN}Persisted {len(room.monsters)} NPCs to room blueprint.{Colors.RESET}")

@command_manager.register("@give", admin=True)
def give_npc_item(player, args):
    """
    Gives an item to an NPC.
    Usage: @give <npc_name> <item_id>
    """
    parts = args.split()
    if len(parts) < 2:
        player.send_line("Usage: @give <npc_name> <item_id>")
        return

    npc_name = parts[0]
    item_id = parts[1]

    # Find NPC
    target = None
    for mob in player.room.monsters:
        if npc_name.lower() in mob.name.lower():
            target = mob
            break

    if not target:
        player.send_line(f"NPC '{npc_name}' not found.")
        return

    # Check if item exists in world
    if item_id not in player.game.world.items:
        player.send_line(f"Item ID '{item_id}' not found in registry.")
        return

    # Create item instance
    proto = player.game.world.items[item_id]
    from models import Item, Armor, Weapon, Consumable
    # This is a bit complex due to different item types... 
    # Let's use a helper if we have one, otherwise create a basic Item.
    # Actually, persistence has item_from_data, but we need the dict.
    
    # Quick fix: Use the prototype.to_dict() if available
    item_data = proto # If it's already a dict
    if hasattr(proto, 'to_dict'):
        item_data = proto.to_dict()
    
    item = persistence.item_from_data(item_data, player.game)
    if item:
        target.inventory.append(item)
        player.send_line(f"Gave {item.name} to {target.name}.")
        player.room.dirty = True
    else:
        player.send_line("Failed to create item instance.")
