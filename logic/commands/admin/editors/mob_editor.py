"""
logic/commands/admin/editors/mob_editor.py
Logic for editing Mobs.
"""
import logic.handlers.command_manager as command_manager
from utilities.colors import Colors
from models import Monster
from .base_editor import _find_mob_everywhere

def _handle_set_mob(player, args, pre_resolved_mob=None):
    if not args: return False, "Usage: @set mob <target> <attr> <value>"
    parts = args.split(maxsplit=2)
    if len(parts) < 3: return False, "Usage: @set mob <target> <attr> <value>"
        
    target_name, attr, value = parts[0], parts[1].lower(), parts[2]
    mob = pre_resolved_mob if pre_resolved_mob else _find_mob_everywhere(player, target_name)
    if not mob: return False, f"Mob '{target_name}' not found."
        
    if attr in ["name", "desc", "description"]:
        real_attr = "description" if attr == "desc" else attr
        setattr(mob, real_attr, value)
    elif attr in ["hp", "max_hp", "damage"]:
        try: setattr(mob, attr, int(value))
        except ValueError: return False, f"{attr} must be an integer."
    elif attr in ["tags", "tag"]:
        mob.tags = [f.strip() for f in value.split(',')]
    elif attr == "flags":
        mob.flags = [f.strip() for f in value.split(',')]
    else:
        return False, f"Unknown mob attribute '{attr}'."

    proto_id = getattr(mob, 'prototype_id', None)
    if proto_id and proto_id in player.game.world.monsters:
        proto = player.game.world.monsters[proto_id]
        target_attr = "description" if attr == "desc" else attr
        if hasattr(proto, target_attr):
            setattr(proto, target_attr, getattr(mob, target_attr))
        return True, f"Updated '{mob.name}' & prototype. (Changes are in memory)"
    return True, f"Updated instance '{mob.name}' (No prototype found)."

def _show_mob_editor_dashboard(player, target):
    player.send_line(f"\n{Colors.BOLD}--- Mob Editor: {target.name} ---{Colors.RESET}")
    player.send_line(f"ID: {getattr(target, 'prototype_id', 'Instance')}")
    fields = [("Name", "name"), ("Desc", "description"), ("HP", "hp"),
              ("Max HP", "max_hp"), ("Damage", "damage"), ("Tags", "tags"), ("Flags", "flags")]
    for label, attr in fields:
        val = getattr(target, attr, "")
        player.send_line(f"{Colors.CYAN}{label:<10}{Colors.RESET}: {val}")
    player.send_line("-" * 40)
    player.send_line(f"Type field and value to edit. Type '{Colors.YELLOW}exit{Colors.RESET}' to finish.")

@command_manager.register("@editmob", admin=True)
def edit_mob_visual(player, args):
    if not args:
        player.send_line("Usage: @editmob <mob_name>")
        return
    target = _find_mob_everywhere(player, args)
    if not target:
        player.send_line(f"Mob '{args}' not found.")
        return
    if not isinstance(target, Monster):
        player.send_line(f"Target '{target.name}' is not a monster.")
        return
    player.state = "mob_editor"
    player.editor_mob = target
    _show_mob_editor_dashboard(player, target)

def handle_mob_editor_input(player, message):
    if not hasattr(player, 'editor_mob'):
        player.send_line("Error: No mob target. Exiting editor.")
        player.state = "normal"
        return

    target = player.editor_mob
    msg = message.strip()
    if not msg: return
    
    cmd_parts = msg.split(maxsplit=1)
    cmd = cmd_parts[0].lower()
    args = cmd_parts[1] if len(cmd_parts) > 1 else ""

    if cmd in ["exit", "quit", "cancel", "done"]:
        player.state = "normal"
        if hasattr(player, 'editor_mob'): del player.editor_mob
        player.send_line("Exited mob editor.")
        return

    dummy_args = f"SELF {cmd} {args}"
    success, result_msg = _handle_set_mob(player, dummy_args, pre_resolved_mob=target)
    player.send_line(result_msg)
    if success:
        _show_mob_editor_dashboard(player, target)
