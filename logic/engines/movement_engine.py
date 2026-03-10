"""
Handles pacing and rhythm for player movement to prevent spamming.
"""
import time
import math
from logic.core import effects
from utilities.colors import Colors
from utilities import telemetry

EXHAUSTION_DURATION = 4.0  # 4.0 seconds
MANDATORY_DELAY_SECONDS = 0.1

# Fallback multipliers if data/terrain.json is missing
TERRAIN_MULTIPLIERS = {
    "road": 1.0,
    "plains": 1.2,
    "forest": 1.8,
    "mountain": 5.0,
    "indoors": 1.0
}

def check_move_pacing(player, room=None):
    """
    Calculates dynamic movement delays based on terrain and status.
    Returns (can_move, reason, wait_time).
    """
    game = getattr(player, 'game', None)
    if not game:
        return True, "OK", 0.0

    current_time = time.time()

    # Initialize Pacing State on the player object if it doesn't exist
    if not hasattr(player, 'move_pacing_state'):
        player.move_pacing_state = {'last_move_time': 0}

    # 1. Calculate Dynamic Delay
    base_delay = MANDATORY_DELAY_SECONDS
    
    # Terrain Multiplier
    terrain_mult = 1.0
    if room:
        terrain = getattr(room, 'terrain', 'road')
        config = getattr(player.game.world, 'terrain_config', {}).get('multipliers', TERRAIN_MULTIPLIERS)
        terrain_mult = config.get(terrain, 1.0)

    # Turtle Stance: Unstoppable (Ignores terrain delay)
    if effects.has_effect(player, "turtle_stance"):
        terrain_mult = 1.0

    delay = base_delay * terrain_mult

    # Exhaustion Penalty
    if effects.has_effect(player, "exhausted"):
        delay *= 3.0

    # 2. Check Timing
    time_since = current_time - player.move_pacing_state.get('last_move_time', 0)
    remaining = delay - time_since

    if remaining > 0:
        if remaining <= 0.05:
            return False, "BUFFER", remaining
        return False, "Input too fast.", remaining

    # 3. Success: Update timestamp
    player.move_pacing_state['last_move_time'] = current_time
    return True, "OK", 0.0

def calculate_move_cost(player, room):
    """
    Calculates the dynamic stamina cost for movement.
    Base: 1 STM
    Modifiers: Terrain, Weight, Stances.
    """
    # Base Cost
    cost = 1.0
    
    # Terrain Modifier
    terrain = getattr(room, 'terrain', 'indoors')
    config = getattr(player.game.world, 'terrain_config', {}).get('multipliers', TERRAIN_MULTIPLIERS)
    cost *= config.get(terrain, 1.0)
    
    # Weight Modifier
    if getattr(player, 'is_heavy', False):
        cost *= 3.0
        
    # Stance Modifiers (The Interceptor)
    if effects.has_effect(player, "crane_stance"):
        cost *= 0.5
    if effects.has_effect(player, "turtle_stance"):
        cost *= 1.5
        
    return int(math.ceil(max(1.0, cost)))
