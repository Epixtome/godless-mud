"""
logic/commands/admin/editors/item_editor.py
Logic for editing Items.
"""
import logic.handlers.command_manager as command_manager
from utilities.colors import Colors
from models import Item
from .base_editor import FIELD_HELP, _find_item_everywhere

def _handle_set_item(player, args, pre_resolved_item=None):
    if not args: return False, "Usage: @set item <target> <attr> <value>"
    parts = args.split(maxsplit=2)
    if len(parts) < 3: return False, "Usage: @set item <target> <attr> <value>"
        
    target_name, attr, value = parts[0], parts[1].lower(), parts[2]
    item = pre_resolved_item if pre_resolved_item else _find_item_everywhere(player, target_name)
    if not item: return False, f"Item '{target_name}' not found."
        
    if attr in ["name", "desc", "description"]:
        real_attr = "description" if attr == "desc" else attr
        setattr(item, real_attr, value)
    elif attr == "slot":
        item.slot = value.lower()
    elif attr in ["value", "defense"]:
        try: setattr(item, attr, int(value))
        except ValueError: return False, f"{attr} must be an integer."
    elif attr == "damage":
        if not hasattr(item, 'damage_dice'): return False, "Item is not a weapon."
        item.damage_dice = value
    elif attr in ["flags", "flag"]:
        tokens = [f.strip() for f in value.replace(',', ' ').split()]
        is_mod = any(t.startswith('+') or t.startswith('-') for t in tokens)
        if is_mod:
            current = set(item.flags)
            for t in tokens:
                if t.startswith('+'): current.add(t[1:])
                elif t.startswith('-'): current.discard(t[1:])
            item.flags = list(current)
        else:
            item.flags = tokens
    elif attr == "scaling":
        try:
            scaling = {}
            for pair in value.split():
                k, v = pair.split(':')
                scaling[k.lower()] = float(v)
            item.scaling = scaling
        except: return False, "Format: tag:val (e.g. fire:1.0 martial:0.5)"
    else:
        return False, f"Unknown item attribute '{attr}'."

    proto_id = getattr(item, 'prototype_id', None)
    if proto_id and proto_id in player.game.world.items:
        proto = player.game.world.items[proto_id]
        target_attr = "description" if attr == "desc" else attr
        if attr == "damage": target_attr = "damage_dice"
        if hasattr(item, target_attr):
            setattr(proto, target_attr, getattr(item, target_attr))
        return True, f"Updated '{item.name}' & prototype. (Unsaved - use @saveitems)"
    return True, f"Updated instance '{item.name}' (No prototype found)."

def _show_editor_dashboard(player, target):
    player.send_line(f"\n{Colors.BOLD}--- Item Editor: {target.name} ---{Colors.RESET}")
    player.send_line(f"ID: {getattr(target, 'prototype_id', 'Instance')}")
    fields = [("Name", "name"), ("Desc", "description"), ("Type", "type"), ("Slot", "slot"),
              ("Damage", "damage_dice"), ("Defense", "defense"), ("Value", "value"),
              ("Scaling", "scaling"), ("Flags", "flags"), ("Effects", "effects")]
    for label, attr in fields:
        val = getattr(target, attr, "")
        player.send_line(f"{Colors.CYAN}{label:<10}{Colors.RESET}: {val}")
    player.send_line("-" * 40)
    player.send_line(f"Type field and value to edit. Type '{Colors.YELLOW}@saveitem{Colors.RESET}' to save.")

@command_manager.register("@edit", admin=True)
def edit_visual(player, args):
    if not args:
        player.send_line("Usage: @edit <item_name>")
        return
    target = _find_item_everywhere(player, args)
    if not target:
        player.send_line(f"Item '{args}' not found.")
        return
    if not isinstance(target, Item) and not hasattr(target, 'value'):
        player.send_line(f"Target '{target.name}' is not an item.")
        return
    player.state = "item_editor"
    player.editor_item = target
    _show_editor_dashboard(player, target)

def handle_editor_input(player, message):
    if not hasattr(player, 'editor_item'):
        player.send_line("Error: No item target. Exiting editor.")
        player.state = "normal"
        return

    target = player.editor_item
    msg = message.strip()
    if not msg: return
    
    cmd_parts = msg.split(maxsplit=1)
    cmd = cmd_parts[0].lower()
    args = cmd_parts[1] if len(cmd_parts) > 1 else ""

    if not args and cmd in FIELD_HELP:
        player.send_line(f"{Colors.YELLOW}Help for '{cmd}':{Colors.RESET}\n{FIELD_HELP[cmd]}")
        return

    if cmd in ["exit", "quit", "cancel", "done"]:
        player.state = "normal"
        if hasattr(player, 'editor_item'): del player.editor_item
        player.send_line("Exited item editor (Unsaved).")
        return
        
    if cmd == "@saveitem" or cmd == "@saveitems":
        from logic.core import loader
        loader.save_items(player.game.world)
        player.state = "normal"
        if hasattr(player, 'editor_item'): del player.editor_item
        player.send_line(f"Saved changes to {target.name} and exited editor.")
        return

    dummy_args = f"SELF {cmd} {args}"
    success, result_msg = _handle_set_item(player, dummy_args, pre_resolved_item=target)
    player.send_line(result_msg)
    if success:
        _show_editor_dashboard(player, target)