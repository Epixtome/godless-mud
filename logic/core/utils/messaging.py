"""
logic/core/utils/messaging.py
Domain: Telnet protocol, output formatting, and prompt construction.
Ensures IAC GA (Go Ahead) compliance and buffer management.
"""
import logging
import time
from datetime import datetime
from typing import TYPE_CHECKING
from utilities.colors import Colors
from logic.constants import Tags

if TYPE_CHECKING:
    from models.entities.player import Player

logger = logging.getLogger("GodlessMUD")

def get_prompt(player):
    """
    Constructs the standard status prompt.
    Includes HP, Stamina, and class-specific pips.
    Dispatched via event_engine for modularity.
    """
    # Base Resources
    parts = [f"{Colors.GREEN}HP: {player.hp}/{player.max_hp}{Colors.RESET}"]
    
    # Universal Stamina
    stm = player.resources.get('stamina', 0)
    max_stm = player.get_max_resource('stamina')
    
    panting = ""
    if "panting" in player.status_effects:
        panting = f" {Colors.RED}(P){Colors.YELLOW}"
        
    parts.append(f"{Colors.YELLOW}STM: {stm}/{max_stm}{panting}{Colors.RESET}")
    
    # Universal Balance (V5.0 Posture)
    bal = player.resources.get('balance', 100)
    max_bal = player.get_max_resource('balance')
    bal_pct = (bal / max_bal) * 100 if max_bal > 0 else 100
    bal_color = Colors.MAGENTA
    if bal_pct < 20: bal_color = Colors.BOLD + Colors.RED # Broken
    elif bal_pct < 50: bal_color = Colors.RED # Unsteady
    parts.append(f"{bal_color}BAL: {bal}/{max_bal}{Colors.RESET}")
    
    # [V7.2] HEAT (Accrued from spells/move)
    heat = player.resources.get(Tags.HEAT, 0)
    if heat > 0:
        h_color = Colors.YELLOW if heat < 50 else Colors.RED
        parts.append(f"{h_color}HEAT: {heat}{Colors.RESET}")

    # Class-Specific Resources (Decoupled: Automated via Registry)
    from logic.core import resource_registry
    kit_id = player.active_kit.get('id') if hasattr(player, 'active_kit') else None
    if kit_id:
        definitions = resource_registry.get_resources_for_kit(kit_id)
        for rd in definitions:
            # Resolve Current Value
            current = 0
            if hasattr(player, 'ext_state') and player.active_class in player.ext_state:
                current = player.ext_state[player.active_class].get(rd.id, 0)
            elif hasattr(player, 'resources'):
                current = player.resources.get(rd.id, 0)
            
            # Resolve Max
            t_max = rd.max
            if rd.max_getter:
                try:
                    t_max = rd.max_getter(player)
                except:
                    pass
            
            # Visibility Gate
            if current > 0 or rd.always_show:
                label = rd.shorthand or rd.display_name[:3].upper()
                parts.append(f"{rd.color}{label}: {current}/{t_max}{Colors.RESET}")

    # Modular Hooks for complex status displays (Stances, etc)
    player.active_statuses_display = []
    from logic.core.engines.event_engine import dispatch
    dispatch("on_build_prompt", {'player': player, 'prompts': player.active_statuses_display})
    
    # Generic Status Effect Display (V4.5)
    if player.status_effects:
        from logic.core import effects
        for eff_id in player.status_effects:
            eff_def = effects.get_effect_definition(eff_id, player.game)
            if isinstance(eff_def, dict):
                # [GCA MODERNIZATION] Dynamic Prompt Visibility
                # Prioritize explicit metadata flag over legacy hardcoded lists
                meta = eff_def.get('metadata', {})
                if isinstance(meta, dict):
                    if meta.get('display_in_prompt') is False or meta.get('hidden') is True:
                        continue
                
                # Group-based exclusion (Stances and Class Passives handled by on_build_prompt)
                if eff_def.get('group') in ['stance', 'class_passive', 'resource']:
                    continue

                name = eff_def.get('short_name') or eff_def.get('name', eff_id)
                name = str(name).title()
                
                # Use display_utils.highlight_status_keywords for consistent coloring
                from logic.core.utils import display_utils
                formatted_name = display_utils.highlight_status_keywords(name)
                
                player.active_statuses_display.append(formatted_name)

    # Ensure all extensions are strings to avoid join errors
    status_str_list = [str(p) for p in player.active_statuses_display]
    parts.extend(status_str_list)
        
    prompt = f"[{' '.join(str(p) for p in parts)}]"
    
    # Combat Target Display
    if player.fighting:
        if player.fighting.hp > 0:
            target = player.fighting
            t_max = getattr(target, 'max_hp', target.hp) or 1
            pct = (target.hp / t_max) * 100
            
            # Condition Scaling
            condition = "Excellent"
            if pct < 15: condition = "Critical"
            elif pct < 30: condition = "Bad"
            elif pct < 50: condition = "Wounded"
            elif pct < 75: condition = "Hurt"
            elif pct < 100: condition = "Scratched"

            # Condition Coloring
            cond_color = Colors.GREEN
            if pct < 15: cond_color = Colors.BOLD + Colors.RED
            elif pct < 30: cond_color = Colors.RED
            elif pct < 50: cond_color = Colors.YELLOW
            elif pct < 75: cond_color = Colors.CYAN
            
            # [V7.2] Dynamic Target Status Display
            statuses = []
            t_effects = getattr(target, 'status_effects', {})
            from logic.core import effects
            for eff_id in t_effects:
                eff_def = effects.get_effect_definition(eff_id, player.game)
                if isinstance(eff_def, dict):
                    meta = eff_def.get('metadata', {})
                    if isinstance(meta, dict) and (meta.get('display_in_prompt') is False or meta.get('hidden') is True):
                        continue
                    if eff_def.get('group') in ['stance', 'class_passive', 'resource']:
                        continue
                        
                    name = eff_def.get('short_name') or eff_def.get('name', eff_id)
                    # Use centralized highlight to determine base color
                    from logic.core.utils import display_utils
                    formatted_name = display_utils.highlight_status_keywords(str(name).upper())
                    statuses.append(formatted_name)

            # Target Balance (Posture)
            t_bal = target.resources.get('balance', 100) if hasattr(target, 'resources') else 100
            t_max_bal = getattr(target, 'get_max_resource', lambda x: 100)('balance')
            bal_pct = (t_bal / t_max_bal) * 100 if t_max_bal > 0 else 100
            bal_color = Colors.MAGENTA
            if bal_pct < 20: bal_color = Colors.BOLD + Colors.RED # Broken
            elif bal_pct < 50: bal_color = Colors.RED # Unsteady
            
            status_str = f" | {' '.join(statuses)}" if statuses else ""
            prompt += f" {Colors.DARK_GRAY}>>{Colors.RESET} {Colors.BOLD}{target.name}{Colors.RESET} [{cond_color}{condition}{Colors.RESET}{status_str}] {bal_color}B:{t_bal}/{t_max_bal}{Colors.RESET}"
    
    # Builder HUD (V7.1)
    if (player.state in ["building", "kit_menu"] or getattr(player, 'is_building', False)) and hasattr(player, 'builder_state'):
        bs = player.builder_state
        from logic.commands.admin.construction.builder_state import _load_kit
        k_data = _load_kit(bs["stencil_set"])
        
        def mode_label(label, value):
            color = Colors.BOLD + Colors.WHITE if value else Colors.DARK_GRAY
            return f"{color}{label}{Colors.RESET}"

        modes = [
            mode_label("Stitch", getattr(player, 'autostitch', False)),
            mode_label("Brush", getattr(player, 'autobrush', False)),
            mode_label("Dig", getattr(player, 'autodig', False))
        ]
        
        elev = getattr(player.room, 'elevation', 0)
        brush_elev = bs.get('brush_elevation', 'Auto')
        builder_line = f"{Colors.DARK_GRAY}[ARCHITECT | Stencil: {Colors.CYAN}{bs['stencil_set']}{Colors.DARK_GRAY} | {' '.join(modes)} | Room: {Colors.WHITE}{elev}{Colors.DARK_GRAY} | Brush: {Colors.YELLOW}{brush_elev}{Colors.DARK_GRAY}]{Colors.RESET}"
        prompt = f"\r\n{builder_line}\r\n{prompt}"
            
    return prompt + " > "

def send_raw(player, message, include_prompt=False):
    """
    The fundamental output pipe. 
    Handles buffering and the critical Telnet Go Ahead (IAC GA) signal.
    [V8.0] Structured JSON delivery for Web Client.
    """
    if getattr(player, 'is_web', False):
        # Structured JSON delivery for Web Client
        try:
            # We don't include prompts in log messages for the web client; 
            # they are sent separately as 'prompt' events.
            data = {
                "type": "log:message",
                "data": {
                    "text": message
                },
                "timestamp": time.time()
            }
            player.send_json(data)
            
            if include_prompt:
                player.send_prompt()
            return
        except Exception as e:
            logger.error(f"GES Web Dispatch Error: {e}")

    # Standard Telnet Path
    if include_prompt:
        # Ensure message ends with a newline before the prompt, without double-padding
        if message and not message.endswith("\n"):
            message += "\r\n"
        message += f"{player.get_prompt()}"

    if player.is_buffering:
        player.output_buffer.append(message)
    else:
        try:
            player.connection.write(message)
            if include_prompt or message.endswith("> "):
                # IAC GA is delegated to connection.flush() 
                player.connection.flush()
        except Exception as e:
            logger.error(f"Error sending to {player.name}: {e}")

def flush(player):
    """Flushes the output buffer and stops buffering."""
    if player.output_buffer:
        full_msg = "".join(player.output_buffer)
        
        if getattr(player, 'is_web', False):
            # Send the entire buffered block as a single event
            player.send_json({
                "type": "log:message", 
                "data": {
                    "text": full_msg
                },
                "timestamp": time.time()
            })
            player.output_buffer = []
            return True

        try:
            player.connection.write(full_msg)
            player.connection.flush()
            player.output_buffer = []
            return True
        except Exception as e:
            logger.error(f"Error flushing to {player.name}: {e}")
    return False

def show_next_page(player):
    """Handles the display of paginated text chunks."""
    PAGE_SIZE = 20
    if not player.pagination_buffer:
        return
    
    chunk = player.pagination_buffer[:PAGE_SIZE]
    player.pagination_buffer = player.pagination_buffer[PAGE_SIZE:]
    
    for line in chunk:
        player.send_line(line)
        
    if player.pagination_buffer:
        if getattr(player, 'is_web', False):
            # Send a pagination signal for the UI to show a 'More' button
            player.send_json({"type": "pagination:more"})
        else:
            player.connection.write("\r\n[Press Enter for more, 'q' to quit] ")

def send_line(player, message, include_prompt=False):
    """Sends a message followed by a newline."""
    if hasattr(player, 'is_auditing') and player.is_auditing:
        # Only timestamp non-empty lines to prevent visual clutter
        if message and str(message).strip():
            ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            message = f"{Colors.DGREY}[{ts}]{Colors.RESET} {message}"
    
    line_end = "\r\n" if not getattr(player, 'is_web', False) else "\n"
    send_raw(player, f"{message}{line_end}", include_prompt=include_prompt)

def broadcast_room(room, message, exclude_player=None):
    """Broadcasts a message to all players in a room."""
    for player in room.players:
        if player != exclude_player:
            send_line(player, message)

def broadcast_global(game, message):
    """Broadcasts a message to all connected players."""
    for player in game.players.values():
        send_line(player, message)

def broadcast_event(game, event_type, payload):
    """
    [V12.3] Sovereign Event Pulse: Broadcasts structured JSON to all Web Clients.
    Used for real-time terrain updates, world shifts, and admin pings.
    """
    import time
    data = {
        "type": event_type,
        "data": payload,
        "timestamp": time.time()
    }
    # [V12.0] Safe Access: Ensure game exists and has players
    if not game:
        return
        
    for player in game.players.values():
        if getattr(player, 'is_web', False):
            try:
                # Direct JSON injection bypassing the log buffer
                player.send_json(data)
            except:
                pass
