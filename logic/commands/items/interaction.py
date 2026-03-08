from logic.handlers import command_manager
from logic.common import find_by_index
from models import Corpse

@command_manager.register("open", category="interaction")
def open_obj(player, args):
    """Open a door or container."""
    if not args:
        player.send_line("Open what?")
        return
        
    # 1. Check Doors
    direction = args.lower()
    if direction in player.room.doors:
        door = player.room.doors[direction]
        if door.state == 'open':
            player.send_line(f"The {door.name} is already open.")
        elif door.state == 'locked':
            player.send_line(f"The {door.name} is locked.")
        else:
            door.state = 'open'
            player.send_line(f"You open the {door.name}.")
            player.room.broadcast(f"{player.name} opens the {door.name}.", exclude_player=player)
            # Sync reciprocal (omitted for brevity/lack of context on helper)
        return

    # 2. Check Items
    target = find_by_index(player.inventory, args)
    if not target:
        target = find_by_index(player.room.items, args)
        
    if target:
        if isinstance(target, Corpse):
            player.send_line("You cannot open a corpse. Just 'get' items from it.")
            return

        if not hasattr(target, 'inventory'):
            player.send_line(f"{target.name} cannot be opened.")
            return
        
        state = getattr(target, 'state', 'open')
        if state == 'open':
            player.send_line(f"{target.name} is already open.")
        elif state == 'locked':
            player.send_line(f"{target.name} is locked.")
        else:
            target.state = 'open'
            player.send_line(f"You open {target.name}.")
            player.room.broadcast(f"{player.name} opens {target.name}.", exclude_player=player)
        return
        
    player.send_line("You don't see that here.")

@command_manager.register("close", category="interaction")
def close_obj(player, args):
    """Close a door or container."""
    if not args:
        player.send_line("Close what?")
        return
        
    # 1. Check Doors
    direction = args.lower()
    if direction in player.room.doors:
        door = player.room.doors[direction]
        if door.state == 'closed':
            player.send_line(f"The {door.name} is already closed.")
        elif door.state == 'locked':
            player.send_line(f"The {door.name} is locked.")
        else:
            door.state = 'closed'
            player.send_line(f"You close the {door.name}.")
            player.room.broadcast(f"{player.name} closes the {door.name}.", exclude_player=player)
        return

    # 2. Check Items
    target = find_by_index(player.inventory, args)
    if not target:
        target = find_by_index(player.room.items, args)
        
    if target:
        if isinstance(target, Corpse):
            player.send_line("You cannot close a corpse.")
            return

        if not hasattr(target, 'inventory'):
            player.send_line(f"{target.name} cannot be closed.")
            return
        
        state = getattr(target, 'state', 'open')
        if state == 'closed':
            player.send_line(f"{target.name} is already closed.")
        else:
            target.state = 'closed'
            player.send_line(f"You close {target.name}.")
            player.room.broadcast(f"{player.name} closes {target.name}.", exclude_player=player)
        return
        
    player.send_line("You don't see that here.")
