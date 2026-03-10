import logic.handlers.command_manager as command_manager
from models import Monster
from logic.core import loader
from utilities.colors import Colors

# Temporary storage for editing sessions: player_name -> dict
EDITING_SESSIONS = {}

@command_manager.register("@createmob", admin=True)
def create_mob(player, args):
    """Create a new mob prototype."""
    if not args:
        player.send_line("Usage: @createmob <id>")
        return
        
    mob_id = args.lower().strip()
    if mob_id in player.game.world.monsters:
        player.send_line(f"Mob ID '{mob_id}' already exists. Use @editmob to modify it.")
        return
        
    # Create default
    new_mob = Monster(
        name="New Mob",
        description="A newly created creature.",
        hp=10,
        damage=1,
        tags=[],
        max_hp=10,
        prototype_id=mob_id
    )
    new_mob.vulnerabilities = {}
    new_mob.states = {}
    new_mob.triggers = []
    new_mob.current_state = "normal"
    new_mob.loadout = []
    
    player.game.world.monsters[mob_id] = new_mob
    
    # Enter Editor
    player.state = "mob_editor"
    EDITING_SESSIONS[player.name] = {"target_id": mob_id, "unsaved": True}
    player.send_line(f"Created mob '{mob_id}'. Entering Mob Editor.")
    _show_editor_status(player, mob_id)

@command_manager.register("@editmob", admin=True)
def edit_mob(player, args):
    """Edit an existing mob prototype."""
    if not args:
        player.send_line("Usage: @editmob <id>")
        return
        
    mob_id = args.lower().strip()
    if mob_id not in player.game.world.monsters:
        player.send_line(f"Mob ID '{mob_id}' not found.")
        return
        
    player.state = "mob_editor"
    EDITING_SESSIONS[player.name] = {"target_id": mob_id, "unsaved": False}
    player.send_line(f"Editing mob '{mob_id}'.")
    _show_editor_status(player, mob_id)

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
    cmd = cmd_parts[0].lower()
    args = " ".join(cmd_parts[1:])

    if cmd == "show":
        _show_editor_status(player, mob_id)
        return
        
    elif cmd == "quit" or cmd == "@quit":
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
        player.send_line("Exited Mob Editor (Changes discarded from disk, but remain in memory until restart).")
        return

    elif cmd == "save":
        success, msg = loader.save_mobs(player.game.world)
        if success:
            session['unsaved'] = False
            player.send_line(f"{Colors.GREEN}Mobs saved to disk.{Colors.RESET}")
        else:
            player.send_line(f"{Colors.RED}Error saving mobs: {msg}{Colors.RESET}")
        return

    elif cmd == "name":
        mob.name = args
        player.send_line(f"Name set to: {mob.name}")
        session['unsaved'] = True

    elif cmd == "desc":
        mob.description = args
        player.send_line("Description updated.")
        session['unsaved'] = True

    elif cmd == "hp":
        if args.isdigit():
            val = int(args)
            mob.max_hp = val
            mob.hp = val
            player.send_line(f"HP set to {val}.")
            session['unsaved'] = True
        else:
            player.send_line("Usage: hp <number>")

    elif cmd == "damage":
        if args.isdigit():
            mob.damage = int(args)
            player.send_line(f"Damage set to {mob.damage}.")
            session['unsaved'] = True
        else:
            player.send_line("Usage: damage <number>")

    elif cmd == "tag":
        # Toggle tag
        tag = args.lower().strip()
        if tag in mob.tags:
            mob.tags.remove(tag)
            player.send_line(f"Removed tag: {tag}")
        else:
            mob.tags.append(tag)
            player.send_line(f"Added tag: {tag}")
        session['unsaved'] = True

    elif cmd == "companion":
        mob.can_be_companion = not getattr(mob, 'can_be_companion', False)
        player.send_line(f"Can be companion: {mob.can_be_companion}")
        session['unsaved'] = True

    elif cmd == "vuln":
        # vuln fire 1.5
        if len(cmd_parts) < 3:
            player.send_line("Usage: vuln <type/skill> <multiplier>")
            return
        
        v_type = cmd_parts[1].lower()
        try:
            mult = float(cmd_parts[2])
            if not hasattr(mob, 'vulnerabilities'): mob.vulnerabilities = {}
            
            if mult == 1.0:
                if v_type in mob.vulnerabilities: del mob.vulnerabilities[v_type]
                player.send_line(f"Removed vulnerability for {v_type}.")
            else:
                mob.vulnerabilities[v_type] = mult
                player.send_line(f"Set {v_type} multiplier to {mult}x.")
            session['unsaved'] = True
        except ValueError:
            player.send_line("Multiplier must be a number.")

    elif cmd == "trigger":
        # trigger hp 50 enraged "roars in fury!"
        # Simplified builder for HP thresholds
        if len(cmd_parts) < 4:
            player.send_line("Usage: trigger hp <pct> <state_name> [msg]")
            return
            
        if cmd_parts[1] == 'hp':
            pct = int(cmd_parts[2])
            state_name = cmd_parts[3]
            msg = " ".join(cmd_parts[4:]) if len(cmd_parts) > 4 else "changes state!"
            
            if not hasattr(mob, 'triggers'): mob.triggers = []
            if not hasattr(mob, 'states'): mob.states = {}
            
            # Create Trigger
            trigger = {"type": "hp_threshold", "value": pct, "action": "set_state", "target": state_name, "fired": False}
            mob.triggers.append(trigger)
            
            # Create State Stub if missing
            if state_name not in mob.states:
                mob.states[state_name] = {"msg": msg, "damage_mult": 1.2}
                
            player.send_line(f"Added HP trigger at {pct}% -> State: {state_name}")
            session['unsaved'] = True

    elif cmd == "loadout":
        # loadout add lantern
        if len(cmd_parts) < 2:
            player.send_line("Usage: loadout add <item_id> | clear")
            return
        
        if cmd_parts[1] == "clear":
            mob.loadout = []
            player.send_line("Loadout cleared.")
        elif cmd_parts[1] == "add" and len(cmd_parts) > 2:
            item_id = cmd_parts[2]
            if not hasattr(mob, 'loadout'): mob.loadout = []
            mob.loadout.append(item_id)
            player.send_line(f"Added {item_id} to loadout.")
        session['unsaved'] = True

    elif cmd == "help":
        player.send_line("Commands: show, name <val>, desc <val>, hp <val>, damage <val>, tag <val>, companion, vuln <type> <mult>, trigger hp <pct> <state>, loadout add <id>, save, quit")
    
    else:
        player.send_line("Unknown editor command. Type 'help'.")

def _show_editor_status(player, mob_id):
    mob = player.game.world.monsters.get(mob_id)
    player.send_line(f"\n{Colors.BOLD}--- Mob Editor: {mob_id} ---{Colors.RESET}")
    player.send_line(f"Name: {mob.name}")
    player.send_line(f"Desc: {mob.description}")
    player.send_line(f"HP: {mob.max_hp} | Damage: {mob.damage}")
    player.send_line(f"Tags: {', '.join(mob.tags)}")
    player.send_line(f"Companion: {getattr(mob, 'can_be_companion', False)}")
    
    if hasattr(mob, 'vulnerabilities') and mob.vulnerabilities:
        player.send_line(f"Vulns: {mob.vulnerabilities}")
    if hasattr(mob, 'triggers') and mob.triggers:
        player.send_line(f"Triggers: {len(mob.triggers)} defined")
    if hasattr(mob, 'loadout') and mob.loadout:
        player.send_line(f"Loadout: {', '.join(mob.loadout)}")
        
    player.send_line(f"{Colors.YELLOW}Type 'help' for commands.{Colors.RESET}")
