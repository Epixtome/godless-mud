import logic.handlers.state_manager as state_manager
import logic.handlers.command_manager as command_manager
from utilities.colors import Colors
import utilities.telemetry as telemetry
import json
import os

# --- Internal Registry ---
_PALETTE_CACHE = {}

def _load_palette(palette_name):
    """Loads a palette from data/blueprints/palettes/"""
    if palette_name in _PALETTE_CACHE:
        return _PALETTE_CACHE[palette_name]
    
    path = f"data/blueprints/palettes/{palette_name}.json"
    if not os.path.exists(path):
        return None
        
    try:
        with open(path, 'r') as f:
            data = json.load(f)
            _PALETTE_CACHE[palette_name] = data
            return data
    except Exception:
        return None

@command_manager.register("@building", admin=True)
def building_mode(player, args):
    """
    Toggles the advanced Building State and HUD.
    Usage: @building [on|off|hud]
    """
    if not hasattr(player, 'builder_state'):
        player.builder_state = {
            "active": False,
            "palette": "default",
            "brush_index": 1,
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
    player.send_line(f"\n{Colors.BOLD}{Colors.CYAN}=== BUILDER STATE ACTIVATED ==={Colors.RESET}")
    player.send_line(f"Palette: {Colors.YELLOW}{player.builder_state['palette']}{Colors.RESET}")
    player.send_line(f"Type '{Colors.BOLD}palette{Colors.RESET}' to see available styles.")
    player.send_line(f"You can now use construction commands ({Colors.BOLD}dig, link, paint{Colors.RESET}) without the {Colors.BOLD}@{Colors.RESET} prefix.")
    player.send_line(f"Type '{Colors.BOLD}exit{Colors.RESET}' to return to normal mode.")
    
    # Log to telemetry for AI context
    telemetry.log_build_action(player, "ENTER_BUILDING_MODE", "Self")

@state_manager.register("building")
def handle_building_input(player, command_line):
    """
    Handles input when the player is in 'building' state.
    Allows for prefix-less admin building commands.
    """
    cmd_line = command_line.strip()
    if not cmd_line: return True
    
    parts = cmd_line.split()
    cmd_name = parts[0].lower()
    args = " ".join(parts[1:]) if len(parts) > 1 else ""

    # 1. Exit Condition
    if cmd_name in ["exit", "quit", "leave"]:
        player.state = "normal"
        if hasattr(player, "builder_state"):
            player.builder_state["active"] = False
        player.send_line(f"{Colors.YELLOW}Exited Building Mode.{Colors.RESET}")
        return True

    # 2. Palette Quick-Select (Numerical)
    if cmd_name.isdigit():
        palette_cmd(player, cmd_name)
        return True

    # 3. Check for building-specific commands (without @)
    # We map common construction commands to their @ versions
    construction_map = {
        "dig": "@dig", "link": "@link", "unlink": "@unlink",
        "paint": "@paint", "paste": "@paste", "brush": "@brush",
        "palette": "@palette", "mark": "@mark", "hud": "@hud",
        "autodig": "@autodig", "auto": "@auto", "copyroom": "@copyroom",
        "deleteroom": "@deleteroom", "stitch": "@stitch", "snapzone": "@snapzone",
        "shiftzone": "@shiftzone", "vision": "@vision", "setlayer": "@setlayer",
        "audit": "@audit", "fixids": "@fixids"
    }

    if cmd_name in construction_map:
        real_cmd = construction_map[cmd_name]
        if real_cmd in command_manager.COMMANDS:
            command_manager.COMMANDS[real_cmd](player, args)
            return True

    # 4. Fall through to normal command handler if it's an @ command
    if cmd_line.startswith("@"):
        return False # Let input_handler handle it

    # 5. Otherwise, assume it's a movement or regular command
    return False

@state_manager.register("palette_menu")
def handle_palette_menu_input(player, command_line):
    """
    Special input handler for the palette menu.
    Allows 1-10 selection then immediately exits back to building state.
    """
    cmd = command_line.strip().lower()
    
    if cmd.isdigit():
        palette_cmd(player, cmd)
        player.state = "building"
        building_hud(player, "") # Refresh HUD after selection
        return True
    
    if cmd in ["exit", "back", "cancel"]:
        player.state = "building"
        player.send_line("Exited palette menu.")
        return True
        
    # Re-show menu if invalid
    palette_cmd(player, "")
    return True

@command_manager.register("@palette", admin=True)
def palette_cmd(player, args):
    """
    Manage building palettes (collections of room templates).
    Usage: @palette [list | load <name> | <index>]
    """
    if not hasattr(player, 'builder_state'):
        building_mode(player, "")

    if not args:
        # Show current palette index
        p_name = player.builder_state.get("palette", "default")
        p_data = _load_palette(p_name)
        
        if not p_data:
            player.send_line(f"Palette '{p_name}' not found. Try '{Colors.BOLD}@palette load basic{Colors.RESET}'")
            return
            
        player.send_line(f"\n{Colors.BOLD}--- Palette: {p_name.upper()} ---{Colors.RESET}")
        for i, item in enumerate(p_data.get("templates", []), 1):
            marker = f"{Colors.GREEN}>>{Colors.RESET}" if i == player.builder_state["brush_index"] else "  "
            player.send_line(f"{i}. {marker} {item['name']} ({item['terrain']})")
        
        player.send_line(f"\nSelect a number {Colors.BOLD}1-{len(p_data.get('templates', []))}{Colors.RESET} or type {Colors.BOLD}exit{Colors.RESET}.")
        player.state = "palette_menu"
        return

    parts = args.split()
    sub = parts[0].lower()

    if sub == "load":
        if len(parts) > 1:
            target = parts[1]
            data = _load_palette(target)
            if data:
                player.builder_state["palette"] = target
                player.builder_state["brush_index"] = 1
                player.send_line(f"Loaded palette: {Colors.CYAN}{target}{Colors.RESET}")
                # Log action
                telemetry.log_build_action(player, "LOAD_PALETTE", target)
            else:
                player.send_line(f"Palette '{target}' not found on disk.")
        else:
            # No target specified, show list (same as 'list' sub-command)
            if not os.path.exists("data/blueprints/palettes/"):
                player.send_line("No palette directory found.")
                return
            files = [f.replace(".json", "") for f in os.listdir("data/blueprints/palettes/") if f.endswith(".json")]
            player.send_line(f"Available Palettes: {', '.join(files)}")
            player.send_line(f"Usage: {Colors.BOLD}palette load <name>{Colors.RESET}")
            
    elif sub == "list":
        if not os.path.exists("data/blueprints/palettes/"):
            player.send_line("No palette directory found.")
            return
        files = [f.replace(".json", "") for f in os.listdir("data/blueprints/palettes/") if f.endswith(".json")]
        player.send_line(f"Available Palettes: {', '.join(files)}")

    elif sub.isdigit():
        idx = int(sub)
        p_data = _load_palette(player.builder_state["palette"])
        if p_data and 1 <= idx <= len(p_data.get("templates", [])):
            player.builder_state["brush_index"] = idx
            template = p_data["templates"][idx-1]
            player.send_line(f"Brush set to: {Colors.YELLOW}{template['name']}{Colors.RESET}")
            # Update legacy brush settings if missing
            if not hasattr(player, 'brush_settings'): player.brush_settings = {}
            player.brush_settings.update(template)
        else:
            player.send_line("Invalid index.")

@command_manager.register("@mark", admin=True)
def mark_cmd(player, args):
    """
    Drops a strategic marker for AI reference.
    Usage: @mark <label> [note]
    Example: @mark frontier_gate "This is where the wall should end."
    """
    if not args:
        player.send_line("Usage: @mark <label> [note]")
        return
        
    parts = args.split(maxsplit=1)
    label = parts[0]
    note = parts[1] if len(parts) > 1 else ""
    
    telemetry.log_build_marker(player, label, note)
    player.send_line(f"{Colors.GREEN}Marker Dropped: {Colors.BOLD}{label}{Colors.RESET}")
    player.send_line(f"AI Context Saved: {player.room.x}, {player.room.y}")

@command_manager.register("@hud", admin=True)
def building_hud(player, args):
    """Refreshes or toggles the builder HUD."""
    if not hasattr(player, 'builder_state') or not player.builder_state["active"]:
        player.send_line("Enter @building mode first.")
        return
        
    p_name = player.builder_state["palette"]
    idx = player.builder_state["brush_index"]
    p_data = _load_palette(p_name)
    
    template_name = "None"
    if p_data and 0 <= idx-1 < len(p_data["templates"]):
        template_name = p_data["templates"][idx-1]["name"]

    player.send_line(f"\n{Colors.BOLD}{Colors.DGREY}[ BUILDER HUD ] Zone: {player.room.zone_id} | Coord: ({player.room.x}, {player.room.y}, {player.room.z}) | Palette: {p_name} | Template: {template_name}{Colors.RESET}")
