from logic.handlers import command_manager
from logic.core import search, resources, items

@command_manager.register("wear", "equip", category="item")
def equip_item(player, args):
    """Equip an item."""
    if not args:
        player.send_line("Equip what?")
        return

    if args.lower() == "all":
        equipped_count = 0
        for item in list(player.inventory):
            if items.equip_item(player, item):
                equipped_count += 1
        
        if equipped_count == 0:
            player.send_line("You have nothing useful to equip (or slots are full).")
        return
        
    item = search.search_list(player.inventory, args)
    if not item:
        player.send_line("You aren't carrying that.")
        return

    items.equip_item(player, item)

@command_manager.register("remove", "unequip", category="item")
def remove_item(player, args):
    """Unequip an item."""
    if not args:
        player.send_line("Remove what?")
        return

    if args.lower() == "all":
        removed_count = 0
        known_attrs = [
            "equipped_weapon", "equipped_offhand", "equipped_armor",
            "equipped_head", "equipped_neck", "equipped_shoulders",
            "equipped_arms", "equipped_hands", "equipped_finger_l",
            "equipped_finger_r", "equipped_legs", "equipped_feet",
            "equipped_floating", "equipped_mount"
        ]
        for attr in known_attrs:
            it = getattr(player, attr, None)
            if it:
                if items.unequip_item(player, it):
                    removed_count += 1
        
        if removed_count == 0:
            player.send_line("You aren't wearing anything.")
        return
    
    # Generic Remove
    known_attrs = [
        "equipped_weapon", "equipped_offhand", "equipped_armor",
        "equipped_head", "equipped_neck", "equipped_shoulders",
        "equipped_arms", "equipped_hands", "equipped_finger_l",
        "equipped_finger_r", "equipped_legs", "equipped_feet",
        "equipped_floating", "equipped_mount"
    ]
    
    for attr in known_attrs:
        it = getattr(player, attr, None)
        if it and (args.lower() in it.name.lower() or args.lower() == it.name.lower()):
            items.unequip_item(player, it)
            return
            
    player.send_line("You aren't equipping that.")
