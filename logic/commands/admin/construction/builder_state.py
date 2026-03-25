"""
logic/commands/admin/construction/builder_state.py
The Professional Building Suite - State & Interface.
Handles Kit management, Stencil selection, and the Builder HUD.
"""
import logic.handlers.state_manager as state_manager
import logic.handlers.command_manager as command_manager
from utilities.colors import Colors
from utilities.mapper import TERRAIN_PLANES, TERRAIN_ELEVS, TERRAIN_MAP
import utilities.telemetry as telemetry
import json
import os

# --- Internal Registry ---
_KIT_CACHE = {}

def _load_kit(kit_name):
    """Loads a building stencil from data/blueprints/stencils/"""
    if kit_name in _KIT_CACHE:
        return _KIT_CACHE[kit_name]
    
    path = f"data/blueprints/stencils/{kit_name}.json"
    if not os.path.exists(path):
        return None
        
    try:
        with open(path, 'r') as f:
            data = json.load(f)
            _KIT_CACHE[kit_name] = data
            return data
    except Exception:
        return None

@command_manager.register("@building", admin=True, category="admin_tools")
def building_mode(player, args):
    """
    Toggles the advanced Building State and Kit Drawer.
    Usage: @building [on|off|hud]
    """
    if not hasattr(player, 'builder_state'):
        player.builder_state = {
            "active": False,
            "stencil_set": "default",
            "stencil_index": 1,
            "auto_link": True,
            "show_hud": True
        }
    
    sub = args.lower() if args else ""
    
    if sub == "off":
        player.builder_state["active"] = False
        player.ignore_fog = False # Restore exploration fog for gameplay
        player.state = "normal"
        player.send_line(f"{Colors.YELLOW}Building Mode: DISABLED{Colors.RESET}")
        return
        
    if sub == "on" or not sub:
        player.builder_state["active"] = True
        player.ignore_fog = True # Builders should always see the canvas
        player.state = "building"
        player.send_line(f"{Colors.GREEN}Building Mode: ENABLED (Vision: ON){Colors.RESET}")
        return
        
    if sub == "hud":
        player.builder_state["show_hud"] = not player.builder_state["show_hud"]
        state = "Enabled" if player.builder_state["show_hud"] else "Disabled"
        player.send_line(f"Builder HUD: {state}")
        return

    # Toggle/On
    player.builder_state["active"] = True
    player.state = "building"
    player.send_line(f"\n{Colors.BOLD}{Colors.CYAN}=== BUILDER ARCHITECT ACTIVATED ==={Colors.RESET}")
    player.send_line(f"Stencil Set: {Colors.YELLOW}{player.builder_state['stencil_set']}{Colors.RESET}")
    player.send_line(f"Type '{Colors.BOLD}kit{Colors.RESET}' or '{Colors.BOLD}drawer{Colors.RESET}' to select stencils.")
    player.send_line(f"Commands ({Colors.BOLD}dig, paint, link{Colors.RESET}) no longer require the '@' prefix.")
    player.send_line(f"Type '{Colors.BOLD}exit{Colors.RESET}' to return to reality.")
    
    telemetry.log_build_action(player, "ENTER_BUILDING_MODE", "Self")

@state_manager.register("building")
def handle_building_input(player, command_line):
    """Input handler for the low-friction 'building' state."""
    cmd_line = command_line.strip()
    if not cmd_line: return True
    
    parts = cmd_line.split()
    cmd_name = parts[0].lower()
    args = " ".join(parts[1:]) if len(parts) > 1 else ""

    if cmd_name in ["exit", "quit", "leave", "normal"]:
        player.state = "normal"
        player.builder_state["active"] = False
        player.send_line(f"{Colors.YELLOW}Exited Architect Mode.{Colors.RESET}")
        return True

    # Kit Selection Shortcut
    if cmd_name.isdigit():
        kit_command(player, cmd_name)
        return True
        
    # Hotkey Stencil Cycling
    if cmd_name in ["[", "]"]:
        k_name = player.builder_state.get("stencil_set", "default")
        k_data = _load_kit(k_name)
        if k_data:
            templates = k_data.get("templates", [])
            idx = player.builder_state.get("stencil_index", 1)
            if cmd_name == "[":
                idx = idx - 1 if idx > 1 else len(templates)
            else:
                idx = idx + 1 if idx < len(templates) else 1
            kit_command(player, str(idx))
        return True

    # Unified architect mapping
    construction_map = {
        "dig": "@auto dig", "link": "@link", "unlink": "@unlink",
        "paint": "@paint", "paste": "@auto paste", "brush": "@auto brush",
        "stitch": "@auto stitch", "vision": "@auto vision", "fog": "@auto vision", 
        "kit": "@kit", "drawer": "@kit", "stencil": "@kit",
        "auto": "@auto", "setlayer": "@setlayer",
        "audit": "@audit", "fixids": "@fixids", "mark": "@mark",
        "furnish": "@furnish", "stamp": "@stamp", "set": "@set",
        "elev": "@set elevation", "elevation": "@set elevation", "z": "@set z",
        "info": "@roominfo", "roominfo": "@roominfo",
        "n": "@architect_move", "s": "@architect_move", "e": "@architect_move", "w": "@architect_move",
        "u": "@architect_move", "d": "@architect_move",
        "north": "@architect_move", "south": "@architect_move", "east": "@architect_move", "west": "@architect_move",
        "up": "@architect_move", "down": "@architect_move"
    }

    if cmd_name in construction_map:
        real_cmd_full = construction_map[cmd_name]
        
        # Split into command and predefined args (v7.0 Fix)
        parts = real_cmd_full.split(maxsplit=1)
        real_cmd = parts[0]
        predefined_args = parts[1] if len(parts) > 1 else ""
        
        # Merge predefined args with user args
        final_args = f"{predefined_args} {args}".strip()
        
        if real_cmd == "@architect_move":
            command_manager.COMMANDS[real_cmd](player, cmd_name)
        else:
            if real_cmd in command_manager.COMMANDS:
                command_manager.COMMANDS[real_cmd](player, final_args)
            else:
                player.send_line(f"{Colors.RED}System Error: Command {real_cmd} not found.{Colors.RESET}")
        return True

    return False

@command_manager.register("@kit", "@stencil", "@drawer", admin=True, category="admin_building")
def kit_command(player, args):
    """
    Open the Stencil Drawer and select architectural patterns.
    Usage: @kit [list | load <name> | <index>]
    (Renamed from 'kits' to 'stencils' to avoid class-kit confusion.)
    """
    if not hasattr(player, 'builder_state'):
        building_mode(player, "")

    k_name = player.builder_state.get("stencil_set", "default")
    k_data = _load_kit(k_name)

    if not args:
        _show_kit_drawer(player, k_name, k_data)
        player.state = "kit_menu"
        return

    parts = args.split()
    sub = parts[0].lower()

    if sub == "load":
        if len(parts) > 1:
            target = parts[1]
            if _load_kit(target):
                player.builder_state["stencil_set"] = target
                player.builder_state["stencil_index"] = 1
                player.autobrush = True # Auto-enable brush mode
                player.send_line(f"{Colors.GREEN}Kit Loaded: {target.upper()}. BRUSH DIPPED in first stencil. Auto-Brush: ON.{Colors.RESET}")
                _show_kit_drawer(player, target, _load_kit(target))
            else:
                player.send_line(f"Kit '{target}' not found in data/blueprints/stencils/")
        else:
            files = [f.replace(".json", "") for f in os.listdir("data/blueprints/stencils/") if f.endswith(".json")]
            player.send_line(f"{Colors.BOLD}Available Kits:{Colors.RESET} {', '.join(files)}")
            
    elif sub == "list":
        files = [f.replace(".json", "") for f in os.listdir("data/blueprints/stencils/") if f.endswith(".json")]
        player.send_line(f"\n{Colors.BOLD}{Colors.CYAN}[ ARCHITECTURAL KITS ]{Colors.RESET}")
        for f in files:
            player.send_line(f" - {f}")
            
    elif sub.isdigit():
        idx = int(sub)
        if k_data and 1 <= idx <= len(k_data.get("templates", [])):
            player.builder_state["stencil_index"] = idx
            stencil = k_data["templates"][idx-1]
            player.autobrush = True # Auto-enable brush mode
            player.builder_state.pop('brush_elevation', None) # Clear manual overrides
            player.send_line(f"{Colors.YELLOW}BRUSH DIPPED in {Colors.BOLD}{stencil['name']}{Colors.RESET} (Auto-Brush: ON)")
            
            # Sync to brush settings for legacy compatibility
            if not hasattr(player, 'brush_settings'): player.brush_settings = {}
            player.brush_settings.update(stencil)
        else:
            player.send_line(f"{Colors.RED}Invalid stencil index.{Colors.RESET}")

def _show_kit_drawer(player, kit_name, kit_data):
    """Displays a premium UI drawer for the stencils."""
    if not kit_data:
        player.send_line(f"{Colors.RED}No kit data for '{kit_name}'.{Colors.RESET}")
        return

    output = []
    output.append(f"\n{Colors.BOLD}{Colors.LIGHT_CYAN}+--------------------------------------------------+{Colors.RESET}")
    output.append(f"{Colors.BOLD}{Colors.LIGHT_CYAN}| {Colors.WHITE}STENCIL DRAWER: {kit_name.upper():<35} {Colors.LIGHT_CYAN}|{Colors.RESET}")
    output.append(f"{Colors.BOLD}{Colors.LIGHT_CYAN}+-----+---+------------------------+-----------------+{Colors.RESET}")
    output.append(f"{Colors.BOLD}{Colors.LIGHT_CYAN}| DIP | S | NAME                   | TERRAIN         |{Colors.RESET}")
    output.append(f"{Colors.BOLD}{Colors.LIGHT_CYAN}+-----+---+------------------------+-----------------+{Colors.RESET}")

    for i, tpl in enumerate(kit_data.get("templates", []), 1):
        is_active = i == player.builder_state.get("stencil_index", 0)
        marker = ">>" if is_active else "  "
        color = Colors.YELLOW if is_active else Colors.WHITE
        
        # Get character from map
        terrain = tpl.get('terrain', 'default')
        raw_symbol = tpl.get('symbol', TERRAIN_MAP.get(terrain, "."))
        symbol = Colors.translate(raw_symbol)
        
        line = f"{Colors.BOLD}{Colors.LIGHT_CYAN}| {color}{i:<3}{marker} {Colors.LIGHT_CYAN}| {symbol} {Colors.LIGHT_CYAN}| {color}{tpl['name']:<22} {Colors.LIGHT_CYAN}| {Colors.DARK_GRAY}{terrain:<15} {Colors.LIGHT_CYAN}|{Colors.RESET}"
        output.append(line)

    output.append(f"{Colors.BOLD}{Colors.LIGHT_CYAN}+-----+---+------------------------+-----------------+{Colors.RESET}")
    output.append(f"{Colors.DARK_GRAY}Select a number to switch stencil, or 'kit load <name>' to swap kits.{Colors.RESET}\n")
    
    player.send_line("\n".join(output))

@state_manager.register("kit_menu")
def handle_kit_menu_input(player, command_line):
    """Menu state for choosing stencils."""
    cmd = command_line.strip().lower()
    
    if cmd.isdigit():
        kit_command(player, cmd)
        player.state = "building"
        return True
    
    if cmd in ["exit", "back", "cancel", "q"]:
        player.state = "building"
        player.send_line("Drawer closed.")
        return True
        
    return False

@command_manager.register("@hud", admin=True, category="admin_tools")
def building_hud(player, args):
    """Pushes a status bar to the user's terminal."""
    if not hasattr(player, 'builder_state'): return
    bs = player.builder_state
    k_data = _load_kit(bs["stencil_set"])
    
    def mode_label(name, active):
        return f"{Colors.GREEN}{name}" if active else f"{Colors.DARK_GRAY}{name}"

    modes = [
        mode_label("Stitch", getattr(player, 'autostitch', False)),
        mode_label("Brush", getattr(player, 'autobrush', False)),
        mode_label("Dig", getattr(player, 'autodig', False))
    ]
    
    elev = getattr(player.room, 'elevation', 0)
    brush_elev = bs.get('brush_elevation', 'Auto')
    builder_line = f"{Colors.DARK_GRAY}[ARCHITECT | Stencil: {Colors.CYAN}{bs['stencil_set']}{Colors.DARK_GRAY} | {' '.join(modes)} | Room: {Colors.WHITE}{elev}{Colors.DARK_GRAY} | Brush: {Colors.YELLOW}{brush_elev}{Colors.DARK_GRAY}]{Colors.RESET}"
    player.send_line(builder_line)

@command_manager.register("@architect_move", admin=True, category="admin_building")
def architect_move(player, args):
    """Special movement handler for the 'Go Ham' building experience."""
    direction = _get_direction_label(args)
    target_room = None
    
    # 1. Check if exit exists
    if direction in player.room.exits:
        target_id = player.room.exits[direction]
        target_room = player.game.world.rooms.get(target_id)
        
        # BRUSH MODE: Update existing room
        if target_room and getattr(player, 'autobrush', False):
            k_data = _load_kit(player.builder_state["stencil_set"])
            if k_data:
                idx = player.builder_state["stencil_index"]
                if 0 < idx <= len(k_data["templates"]):
                    stencil = k_data["templates"][idx-1]
                    import logic.commands.admin.construction.utils as const_utils
                    if stencil:
                        # Pop internal keys to avoid TypeError in update_room
                        s_copy = dict(stencil)
                        s_copy.pop('id', None)
                        s_copy.pop('z_offset', None)
                        
                        # Apply Manual Brush Overrides (V7.0 Persistence)
                        if 'brush_elevation' in player.builder_state:
                            s_copy['elevation'] = player.builder_state['brush_elevation']
                            
                        const_utils.update_room(target_room, **s_copy)
                        
                    player.send_line(f"{Colors.YELLOW}[Brushed] {target_room.name}{Colors.RESET} (Elev: {target_room.elevation})")
    else:
        # DIG MODE: Create room if autodig is on
        if getattr(player, 'autodig', False):
            command_manager.COMMANDS["@dig"](player, direction)
            # Re-read target since @dig just created it
            if direction in player.room.exits:
                 target_id = player.room.exits[direction]
                 target_room = player.game.world.rooms.get(target_id)

    # 2. Perform Movement
    if target_room:
        player.room.players.remove(player)
        target_room.players.append(player)
        player.room = target_room
        command_manager.COMMANDS["look"](player, "")
    else:
        # standard move if not digging
        player.send_line("You cannot go that way. (Use 'auto dig on' to expand)")

@command_manager.register("@mark", admin=True, category="admin_tools")
def mark_cmd(player, args):
    """Dropped marker for AI reference."""
    if not args: return
    telemetry.log_build_marker(player, args, "")
    player.send_line(f"{Colors.GREEN}Marker Dropped: {Colors.BOLD}{args}{Colors.RESET}")

def _get_direction_label(cmd_name):
    d = {"n": "north", "s":"south", "e":"east", "w":"west", "u":"up", "d":"down"}
    return d.get(cmd_name, cmd_name)
