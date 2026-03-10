"""
logic/core/utils/player_logic.py
Sharded logic for Player entity to maintain 300-line compliance.
Handles resource calculation and pacing.
"""
import time
from logic import calibration
from logic.constants import Tags
from utilities.colors import Colors

def get_max_hp(player):
    """Calculates Max HP based on kit and internal constants."""
    kit_name = player.active_kit.get('name', '').lower()
    if kit_name == 'wanderer':
        return 150
    return calibration.MaxValues.HP

def get_max_resource(player, resource_name):
    """Calculates max resource values for specific kits/classes."""
    if resource_name == 'chi': 
        return player.active_kit.get('max_chi', 5)
    
    if resource_name == Tags.HEAT:
        return player.active_kit.get('max_heat', 100)
            
    return 100

def reset_resources(player):
    """Fully restores and resets all resources to base state."""
    player.hp = player.max_hp
    if 'concentration' in player.resources:
        player.resources['concentration'] = get_max_resource(player, 'concentration')
    if Tags.HEAT in player.resources:
        player.resources[Tags.HEAT] = 0
    if 'stability' in player.resources:
        player.resources['stability'] = get_max_resource(player, 'stability')
    if 'chi' in player.resources:
        player.resources['chi'] = 0
    if 'stamina' in player.resources:
        player.resources['stamina'] = get_max_resource(player, 'stamina')
    
    player.send_line(f"{Colors.CYAN}Your vitals and resources have been reset.{Colors.RESET}")

def refresh_tokens(player):
    """Refills movement tokens based on time elapsed (Kinetic Pacing)."""
    current_time = time.time()
    delta = current_time - player.last_refill_time
    
    REFILL_RATE = 4.0 # Comfortable Walk Speed
    player.move_tokens = min(5.0, player.move_tokens + (delta * REFILL_RATE))
    player.last_refill_time = current_time
