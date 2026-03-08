from logic.handlers import command_manager
from logic.core import loader
from models import Item, Weapon, Armor, Consumable

@command_manager.register("@create", category="builder", admin=True)
def create_item(player, args):
    """
    Create a new item prototype from scratch.
    Usage: @create <id> <type> <name>
    Types: weapon, armor, consumable, item
    """
    if not args:
        player.send_line("Usage: @create <id> <type> <name>")
        return
        
    parts = args.split(maxsplit=2)
    if len(parts) < 3:
        player.send_line("Usage: @create <id> <type> <name>")
        return
        
    item_id, item_type, item_name = parts[0], parts[1].lower(), parts[2]
    
    world = player.game.world
    if item_id in world.items:
        player.send_line(f"Error: Item ID '{item_id}' already exists.")
        return
        
    valid_types = ["weapon", "armor", "consumable", "item"]
    if item_type not in valid_types:
        player.send_line(f"Invalid type. Must be one of: {', '.join(valid_types)}")
        return
        
    new_item = None
    # Instantiate with safe defaults
    if item_type == "weapon":
        new_item = Weapon(item_name, "A newly created weapon.", "1d6", {}, None, 0, [], prototype_id=item_id, tags=[])
    elif item_type == "armor":
        new_item = Armor(item_name, "A newly created armor.", 1, None, 0, [], prototype_id=item_id, tags=[])
    elif item_type == "consumable":
        new_item = Consumable(item_name, "A newly created consumable.", {}, 0, [], prototype_id=item_id, tags=[])
    else:
        new_item = Item(item_name, "A newly created item.", 0, [], prototype_id=item_id, tags=[])
        
    # Add to world prototypes
    world.items[item_id] = new_item
    
    # Note: We do NOT save to disk automatically anymore.
    # This prevents partial edits from breaking the file and improves performance.
    
    player.send_line(f"Created item '{item_name}' ({item_id}) in memory.")
    player.send_line(f"Use '@edit {item_name}' to modify it.")
    player.send_line("Remember to use '@saveitems' to persist changes to disk.")
    
    # Give one to player
    instance = new_item.clone()
    player.inventory.append(instance)

@command_manager.register("@saveitems", "@saveitem", category="builder", admin=True)
def save_items_command(player, args):
    """
    Saves all item prototypes to data/items.json.
    Use this after creating or editing items.
    """
    success, msg = loader.save_items(player.game.world)
    player.send_line(msg)