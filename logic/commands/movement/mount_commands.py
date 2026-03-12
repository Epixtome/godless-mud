"""
logic/commands/movement/mount_commands.py
Logic for mounting and dismounting entities.
"""
from logic.handlers import command_manager
from logic.core import search

@command_manager.register("mount", category="movement")
def mount(player, args):
    """Mount up."""
    if not args:
        player.send_line("Mount what?")
        return

    if getattr(player, 'is_mounted', False):
        player.send_line("You are already mounted.")
        return

    target = search.find_living(player.room, args)
    if not target:
        player.send_line("You don't see that here.")
        return

    if "mount" not in getattr(target, 'tags', []):
        player.send_line(f"You cannot mount {target.name}.")
        return

    player.is_mounted = True
    player.mount = target
    player.send_line(f"You swing onto {target.name}.")
    player.room.broadcast(f"{player.name} mounts {target.name}.", exclude_player=player)

@command_manager.register("dismount", category="movement")
def dismount(player, args):
    """Dismount."""
    if not getattr(player, 'is_mounted', False):
        player.send_line("You are not mounted.")
    else:
        player.is_mounted = False
        player.mount = None
        player.send_line("You dismount.")
        player.room.broadcast(f"{player.name} dismounts.", exclude_player=player)
