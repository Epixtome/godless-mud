"""
logic/commands/admin/editors/mob_editor.py
Advanced session-based Mob Editor and attribute setting utility.
"""
from models import Monster
from logic.core import loader, search
import logic.handlers.command_manager as command_manager
from utilities.colors import Colors
from .base_editor import _find_mob_everywhere

# Temporary storage for editing sessions: player_name -> dict
EDITING_SESSIONS = {}

def update_mob_attribute(mob, attr, value):
    """
    Updates a specific attribute on a mob and its prototype if it exists.
    Returns (success, message).
    """
    attr = attr.lower().strip()
    
    if attr in ["name", "desc", "description"]:
        real_attr = "description" if attr in ["desc", "description"] else "name"
        setattr(mob, real_attr, value)
    elif attr in ["hp", "max_hp", "damage", "mitigation", "conceal", "perception"]:
        # Conceal and Perception map to base_*
        real_attr = attr
        if attr == "mitigation": real_attr = "base_mitigation"
        elif attr == "conceal": real_attr = "base_concealment"
        elif attr == "perception": real_attr = "base_perception"
        
        try: setattr(mob, real_attr, int(value))
        except ValueError: return False, f"{attr} must be an integer."
    elif attr in ["tags", "tag"]:
        # Handle +tag, -tag, or comma-sep list
        val_clean = value.strip()
        if val_clean.startswith('+'):
            tag_val = val_clean[1:].strip()
            if tag_val not in mob.tags: mob.tags.append(tag_val)
        elif val_clean.startswith('-'):
            tag_val = val_clean[1:].strip()
            if tag_val in mob.tags: mob.tags.remove(tag_val)
        elif val_clean.lower().startswith('add '):
            tag_val = val_clean[4:].strip()
            if tag_val not in mob.tags: mob.tags.append(tag_val)
        elif val_clean.lower().startswith('remove '):
            tag_val = val_clean[7:].strip()
            if tag_val in mob.tags: mob.tags.remove(tag_val)
        else:
            mob.tags = [f.strip() for f in value.split(',')]
        mob.tags_are_dirty = True
    elif attr == "flags":
        mob.flags = [f.strip() for f in value.split(',')]
    elif attr == "class":
        mob.active_class = value.lower().strip()
        mob.refresh_class()
    elif attr == "shop":
        mob.is_shopkeeper = (value.lower() == "true")
    else:
        return False, f"Unknown mob attribute '{attr}'."

    # Success, now check prototype (handled in _handle_set_mob for contextual safety)
    return True, f"Updated {attr} to: {value}"

def _handle_set_mob(player, args, pre_resolved_mob=None):
    """Entry point for @set mob."""
    if not args: return False, "Usage: @set mob <target> <attr> <value>"
    parts = args.split(maxsplit=2)
    if len(parts) < 3: return False, "Usage: @set mob <target> <attr> <value>"
        
    target_name, attr, value = parts[0], parts[1].lower(), parts[2]
    mob = pre_resolved_mob if pre_resolved_mob else _find_mob_everywhere(player, target_name)
    if not mob: return False, f"Mob '{target_name}' not found."
    
    # Use the workhorse
    success, msg = update_mob_attribute(mob, attr, value)
    
    # Protocol: If it has a prototype, update that too
    proto_id = getattr(mob, 'prototype_id', None)
    if success and proto_id and proto_id in player.game.world.monsters:
        proto = player.game.world.monsters[proto_id]
        update_mob_attribute(proto, attr, value)
        return True, f"{msg} (Instance & Prototype updated)"
        
    return success, msg

@command_manager.register("@editmob", admin=True, category="admin_building")
def edit_mob_visual(player, args):
    """
    Entrance to the visual mob editor.
    Used by @editmob and @set mob.
    """
    from logic.core import search
    if not args:
        # List mobs in current room for quick selection
        if not player.room.monsters:
            player.send_line("Usage: @editmob <id> | <index> | <name>")
            return
        player.send_line("\nVisible Mobs (Use @editmob #<index>):")
        for idx, m in enumerate(player.room.monsters, 1):
            proto_id = getattr(m, 'prototype_id', 'Instance')
            player.send_line(f"  #{idx} {m.name} ({proto_id})")
        return
        
    mob_id = None
    
    # 1. Index Targeting (#1)
    if args.startswith("#") and args[1:].isdigit():
        idx = int(args[1:]) - 1
        if 0 <= idx < len(player.room.monsters):
            mob_id = getattr(player.room.monsters[idx], 'prototype_id', None)
    
    # 2. Prioritize Mobs in Room (By Name)
    if not mob_id:
        target = args.lower().strip()
        room_matches = search.find_matches(player.room.monsters, target)
        if len(room_matches) == 1:
            mob_id = getattr(room_matches[0], 'prototype_id', None)
        elif len(room_matches) > 1:
            player.send_line(f"Multiple matches in room. Specify index (e.g., @editmob #1):")
            for idx, m in enumerate(room_matches, 1):
                player.send_line(f"  #{idx} {m.name} ({getattr(m, 'prototype_id', 'N/A')})")
            return

    # 3. Global Prototype Search
    if not mob_id:
        target = args.lower().strip()
        if target in player.game.world.monsters:
            mob_id = target
        else:
            matches = search.find_matches(player.game.world.monsters.values(), target)
            if len(matches) == 1:
                mob_id = matches[0].id if hasattr(matches[0], 'id') else getattr(matches[0], 'prototype_id', None)
            elif len(matches) > 1:
                player.send_line(f"Multiple prototypes match '{target}':")
                for m in matches[:5]:
                    player.send_line(f"  {getattr(m, 'prototype_id', 'N/A')} ({m.name})")
                return

    if not mob_id or mob_id not in player.game.world.monsters:
        player.send_line(f"Mob candidate '{args}' not found.")
        return
        
    player.state = "mob_editor"
    EDITING_SESSIONS[player.name] = {"target_id": mob_id, "unsaved": False}
    player.send_line(f"Editing mob '{mob_id}'. (Type 'help' for commands)")
    show_editor_status(player, mob_id)

def handle_mob_editor_input(player, command):
    """Handles input while in mob_editor state."""
    session = EDITING_SESSIONS.get(player.name)
    if not session:
        player.state = "normal"
        player.send_line("Editor session lost.")
        return

    mob_id = session['target_id']
    mob = player.game.world.monsters.get(mob_id)
    
    if not mob:
        player.send_line("Mob prototype not found.")
        player.state = "normal"
        return

    cmd_parts = command.split()
    if not cmd_parts: return
    cmd = cmd_parts[0].lower()
    args = " ".join(cmd_parts[1:])

    if cmd == "show":
        show_editor_status(player, mob_id)
        return
        
    elif cmd in ["quit", "@quit", "exit"]:
        if session.get('unsaved'):
            player.send_line("Warning: You have unsaved changes. Use 'save' or 'quit!' to discard.")
        else:
            player.state = "normal"
            del EDITING_SESSIONS[player.name]
            player.send_line("Exited Mob Editor.")
        return

    elif cmd == "quit!":
        player.state = "normal"
        del EDITING_SESSIONS[player.name]
        player.send_line("Exited Mob Editor (Changes discarded).")
        return

    elif cmd == "save":
        success, msg = loader.save_mobs(player.game.world)
        if success:
            session['unsaved'] = False
            player.send_line(f"{Colors.GREEN}Mobs saved to disk.{Colors.RESET}")
        else:
            player.send_line(f"{Colors.RED}Error saving mobs: {msg}{Colors.RESET}")
        return

    # Use the attribute update logic
    success, msg = update_mob_attribute(mob, cmd, args)
    if success:
        player.send_line(msg)
        session['unsaved'] = True
    else:
        # Check for specialized commands
        if cmd == "shout" and len(cmd_parts) >= 3:
            s_type = cmd_parts[1].lower()
            m_text = " ".join(cmd_parts[2:])
            if not hasattr(mob, 'shouts'): mob.shouts = {}
            if s_type not in mob.shouts: mob.shouts[s_type] = []
            mob.shouts[s_type].append(m_text)
            player.send_line(f"Added {s_type} shout.")
            session['unsaved'] = True
        elif cmd == "loot" and len(cmd_parts) >= 3:
            if cmd_parts[1] == "add":
                if not hasattr(mob, 'loot_table'): mob.loot_table = []
                mob.loot_table.append(cmd_parts[2])
                player.send_line(f"Added {cmd_parts[2]} to loot.")
                session['unsaved'] = True
        elif cmd == "quest" and len(cmd_parts) >= 3:
            if cmd_parts[1] == "add":
                if not hasattr(mob, 'quests'): mob.quests = []
                mob.quests.append(cmd_parts[2])
                player.send_line(f"Added quest {cmd_parts[2]}.")
                session['unsaved'] = True
        elif cmd == "help":
            cmds = [
                "show", "name <val>", "desc <val>", "hp <val>", "damage <val>", "tag [+/-]<val>",
                "class <val>", "mitigation <val>", "conceal <val>", "perception <val>",
                "companion", "shop", "shout <type> <msg>", "loot add <id>",
                "vuln <type> <mult>", "trigger hp <pct> <state>", "loadout add <id>", "save", "quit"
            ]
            player.send_line(f"{Colors.YELLOW}Commands:{Colors.RESET} " + ", ".join(cmds))
        else:
            player.send_line(msg)

def show_editor_status(player, mob_id):
    mob = player.game.world.monsters.get(mob_id)
    if not mob: return
    player.send_line(f"\n{Colors.BOLD}--- Mob Editor: {mob_id} ---{Colors.RESET}")
    player.send_line(f"Name: {mob.name}")
    player.send_line(f"Desc: {mob.description}")
    player.send_line(f"HP: {mob.max_hp} | Damage: {mob.damage}")
    player.send_line(f"Tags: {', '.join(mob.tags)}")
    player.send_line(f"Class: {getattr(mob, 'active_class', 'None')} | Shopkeeper: {getattr(mob, 'is_shopkeeper', False)}")
    player.send_line(f"Mitigation: {getattr(mob, 'base_mitigation', 0)} | Conceal: {getattr(mob, 'base_concealment', 0)} | Perception: {getattr(mob, 'base_perception', 10)}")
    player.send_line(f"Companion: {getattr(mob, 'can_be_companion', False)}")
    if hasattr(mob, 'shouts') and mob.shouts: player.send_line(f"Shouts: {', '.join(mob.shouts.keys())}")
    if hasattr(mob, 'vulnerabilities') and mob.vulnerabilities: player.send_line(f"Vulns: {mob.vulnerabilities}")
    if hasattr(mob, 'triggers') and mob.triggers: player.send_line(f"Triggers: {len(mob.triggers)} defined")
    if hasattr(mob, 'loot_table') and mob.loot_table: player.send_line(f"Loot: {len(mob.loot_table)} items")
    if hasattr(mob, 'loadout') and mob.loadout: player.send_line(f"Loadout: {', '.join(mob.loadout)}")
    player.send_line(f"{Colors.YELLOW}Type 'help' for commands.{Colors.RESET}")
