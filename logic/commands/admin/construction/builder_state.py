"""
logic/commands/admin/construction/builder_state.py
The Professional Building Suite - State & Interface.
Handles Kit management, Stencil selection, and the Builder HUD.
"""
import logic.handlers.state_manager as state_manager
import logic.handlers.command_manager as command_manager
from utilities.colors import Colors
from utilities.mapper import TERRAIN_MAP
import utilities.telemetry as telemetry
import json
import os

# --- Internal Registry ---
_KIT_CACHE = {}

def _load_kit(kit_name):
    """Loads a building kit from data/blueprints/kits/"""
    if kit_name in _KIT_CACHE:
        return _KIT_CACHE[kit_name]
    
    path = f"data/blueprints/kits/{kit_name}.json"
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
            "kit": "default",
            "stencil_index": 1,
            "auto_link": True,
            "show_hud": True
        }
    
    sub = args.lower() if args else ""
    
    if sub == "off":
        player.builder_state["active"] = False
        player.state = "normal"
        player.send_line(f"{Colors.YELLOW}Building Mode: DISABLED{Colors.RESET}")
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
    player.send_line(f"Kit: {Colors.YELLOW}{player.builder_state['kit']}{Colors.RESET}")
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

    # Unified architect mapping
    construction_map = {
        "dig": "@dig", "link": "@link", "unlink": "@unlink",
        "paint": "@paint", "paste": "@paste", "brush": "@brush",
        "kit": "@kit", "drawer": "@kit", "stencil": "@kit",
        "auto": "@auto", "vision": "@vision", "setlayer": "@setlayer",
        "audit": "@audit", "fixids": "@fixids", "mark": "@mark",
        "furnish": "@furnish", "stamp": "@stamp"
    }

    if cmd_name in construction_map:
        real_cmd = construction_map[cmd_name]
        command_manager.COMMANDS[real_cmd](player, args)
        return True

    return False

@command_manager.register("@kit", "@stencil", "@drawer", admin=True, category="admin_building")
def kit_command(player, args):
    """
    Open the Kit Drawer and select architectural stencils.
    Usage: @kit [list | load <name> | <index>]
    """
    if not hasattr(player, 'builder_state'):
        building_mode(player, "")

    k_name = player.builder_state.get("kit", "default")
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
                player.builder_state["kit"] = target
                player.builder_state["stencil_index"] = 1
                player.send_line(f"{Colors.GREEN}Kit Loaded: {Colors.BOLD}{target}{Colors.RESET}")
                _show_kit_drawer(player, target, _load_kit(target))
            else:
                player.send_line(f"Kit '{target}' not found in data/blueprints/kits/")
        else:
            files = [f.replace(".json", "") for f in os.listdir("data/blueprints/kits/") if f.endswith(".json")]
            player.send_line(f"{Colors.BOLD}Available Kits:{Colors.RESET} {', '.join(files)}")
            
    elif sub == "list":
        files = [f.replace(".json", "") for f in os.listdir("data/blueprints/kits/") if f.endswith(".json")]
        player.send_line(f"\n{Colors.BOLD}{Colors.CYAN}[ ARCHITECTURAL KITS ]{Colors.RESET}")
        for f in files:
            player.send_line(f" - {f}")
            
    elif sub.isdigit():
        idx = int(sub)
        if k_data and 1 <= idx <= len(k_data.get("templates", [])):
            player.builder_state["stencil_index"] = idx
            stencil = k_data["templates"][idx-1]
            player.send_line(f"{Colors.YELLOW}Stencil Selected: {Colors.BOLD}{stencil['name']}{Colors.RESET}")
            
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
    output.append(f"\n{Colors.BOLD}{Colors.LIGHT_CYAN}┌──────────────────────────────────────────────────┐{Colors.RESET}")
    output.append(f"{Colors.BOLD}{Colors.LIGHT_CYAN}│ {Colors.WHITE}KIT DRAWER: {kit_name.upper():<35} {Colors.LIGHT_CYAN}│{Colors.RESET}")
    output.append(f"{Colors.BOLD}{Colors.LIGHT_CYAN}├────┬───┬────────────────────────┬─────────────────┤{Colors.RESET}")
    output.append(f"{Colors.BOLD}{Colors.LIGHT_CYAN}│ ID │ S │ NAME                   │ TERRAIN         │{Colors.RESET}")
    output.append(f"{Colors.BOLD}{Colors.LIGHT_CYAN}├────┼───┼────────────────────────┼─────────────────┤{Colors.RESET}")

    for i, tpl in enumerate(kit_data.get("templates", []), 1):
        is_active = i == player.builder_state.get("stencil_index", 0)
        marker = ">>" if is_active else "  "
        color = Colors.YELLOW if is_active else Colors.WHITE
        
        # Get character from map
        terrain = tpl.get('terrain', 'default')
        symbol = tpl.get('symbol', TERRAIN_MAP.get(terrain, "."))
        
        line = f"{Colors.BOLD}{Colors.LIGHT_CYAN}│ {color}{i:<2}{marker} {Colors.LIGHT_CYAN}│ {symbol} {Colors.LIGHT_CYAN}│ {color}{tpl['name']:<22} {Colors.LIGHT_CYAN}│ {Colors.DARK_GRAY}{terrain:<15} {Colors.LIGHT_CYAN}│{Colors.RESET}"
        output.append(line)

    output.append(f"{Colors.BOLD}{Colors.LIGHT_CYAN}└────┴───┴────────────────────────┴─────────────────┘{Colors.RESET}")
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
    k_data = _load_kit(bs["kit"])
    
    stencil_name = "None"
    if k_data and 0 < bs["stencil_index"] <= len(k_data["templates"]):
        stencil_name = k_data["templates"][bs["stencil_index"]-1]["name"]
        
    status = f"{Colors.BOLD}{Colors.DARK_GRAY}[ ARCHITECT | Kit: {Colors.CYAN}{bs['kit']}{Colors.DARK_GRAY} | Stencil: {Colors.YELLOW}{stencil_name}{Colors.DARK_GRAY} | Pos: {player.room.x},{player.room.y},{player.room.z} ]{Colors.RESET}"
    player.send_line(status)

@command_manager.register("@mark", admin=True, category="admin_tools")
def mark_cmd(player, args):
    """Dropped marker for AI reference."""
    if not args: return
    telemetry.log_build_marker(player, args, "")
    player.send_line(f"{Colors.GREEN}Marker Dropped: {Colors.BOLD}{args}{Colors.RESET}")
