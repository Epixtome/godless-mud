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
    parts.append(f"{Colors.MAGENTA}BAL: {bal}/{max_bal}{Colors.RESET}")

    # Class-Specific Resources (Decoupled via Events)
    # Individual class modules (Mage, Monk, etc) now subscribe to 'on_build_prompt' 
    # to inject their specific resource displays.

    # Modular Hooks
    player.active_statuses_display = []
    from logic.core.engines.event_engine import dispatch
    dispatch("on_build_prompt", {'player': player, 'prompts': player.active_statuses_display})
    
    # Generic Status Effect Display (V4.5)
    if player.status_effects:
        from logic.core import effects
        for eff_id in player.status_effects:
            # Skip internal/class resources already handled by on_build_prompt
            if eff_id in ['crane_stance', 'turtle_stance', 'magic_shield']:
                continue
            
            eff_def = effects.get_effect_definition(eff_id, player.game)
            if eff_def:
                name = eff_def.get('short_name') or eff_def.get('name', eff_id).title()
                # Determine color based on type
                color = Colors.YELLOW
                if eff_id in effects.HARD_DEBUFFS or eff_id in effects.CRITICAL_STATES:
                    color = Colors.RED
                elif eff_id in effects.SOFT_DEBUFFS:
                    color = Colors.YELLOW # Default to yellow if orange is missing
                
                player.active_statuses_display.append(f"{color}{name}{Colors.RESET}")

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
            
            condition = "Excellent"
            if pct < 15: condition = "Critical"
            elif pct < 30: condition = "Bad"
            elif pct < 50: condition = "Wounded"
            elif pct < 75: condition = "Hurt"
            elif pct < 100: condition = "Scratched"
            
            statuses = []
            t_effects = getattr(target, 'status_effects', {})
            if "off_balance" in t_effects: statuses.append(f"{Colors.MAGENTA}Off-Balance{Colors.RESET}")
            if "stun" in t_effects: statuses.append(f"{Colors.YELLOW}Stunned{Colors.RESET}")
            if "dazed" in t_effects: statuses.append(f"{Colors.YELLOW}Dazed{Colors.RESET}")

            # Target Balance (Posture)
            t_bal = target.resources.get('balance', 100) if hasattr(target, 'resources') else 100
            t_max_bal = getattr(target, 'get_max_resource', lambda x: 100)('balance')
            
            status_str = f" ({'/'.join(statuses)})" if statuses else ""
            prompt += f" ({target.name} [{condition}] BAL: {t_bal}/{t_max_bal}{status_str})"
            
    return prompt + " > "

def send_raw(player, message, include_prompt=False):
    """
    The fundamental output pipe. 
    Handles buffering and the critical Telnet Go Ahead (IAC GA) signal.
    """
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
        player.connection.write("\r\n[Press Enter for more, 'q' to quit] ")

def send_line(player, message, include_prompt=False):
    """Sends a message followed by a newline."""
    if hasattr(player, 'is_auditing') and player.is_auditing:
        # Only timestamp non-empty lines to prevent visual clutter
        if message and str(message).strip():
            ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            message = f"{Colors.DGREY}[{ts}]{Colors.RESET} {message}"
    send_raw(player, f"{message}\r\n", include_prompt=include_prompt)

def broadcast_room(room, message, exclude_player=None):
    """Broadcasts a message to all players in a room."""
    for player in room.players:
        if player != exclude_player:
            send_line(player, message)
