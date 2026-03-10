"""
logic/core/utils/status_logic.py
Internal logic for command blocking and status evaluation.
"""
import logging
from logic.core.utils.status_definitions import CORE_STATUS_DEFINITIONS

logger = logging.getLogger("GodlessMUD")

def is_movement_command(cmd_name: str) -> bool:
    """Checks if a command is for movement."""
    return cmd_name in ["n", "s", "e", "w", "u", "d", "north", "south", "east", "west", "up", "down", "ne", "nw", "se", "sw", "enter", "leave", "move", "flee"]

def is_combat_command(cmd_name: str) -> bool:
    """Checks if a command is for combat."""
    return cmd_name in ["kill", "k", "attack", "hit", "cast", "shoot", "throw"]

def _is_skill_command(player, cmd_name: str) -> bool:
    """Checks if a command string corresponds to an equipped skill or casting command."""
    if cmd_name in ["cast", "sing"]:
        return True
    if not hasattr(player, 'equipped_blessings'):
        return False
    return any(b.id == cmd_name or b.name.strip().lower() == cmd_name for b_id in player.equipped_blessings if (b := player.game.world.blessings.get(b_id)))

def is_action_blocked(player, cmd_name: str, get_defn_func) -> tuple[bool, str | None]:
    """
    Checks if current status effects block the attempted command.
    Returns (True, Reason) or (False, None).
    """
    if not hasattr(player, 'game') or not player.game:
        return False, None

    cmd_name = cmd_name.lower().strip()
    active_effects = getattr(player, 'status_effects', {})

    for effect_id in active_effects:
        effect_def = get_defn_func(effect_id, player.game)
        if not effect_def:
            logger.error(f"Status definition missing for ID: {effect_id} on player {player.name}")
            continue

        blocked_types = effect_def.get('blocks', [])
        effect_name = effect_def.get('name', effect_id.replace('_', ' '))

        if "movement" in blocked_types and is_movement_command(cmd_name):
            return True, f"You cannot move while {effect_name.lower()}!"
        if "combat" in blocked_types and is_combat_command(cmd_name):
            return True, f"You cannot fight while {effect_name.lower()}!"
        if "skills" in blocked_types and _is_skill_command(player, cmd_name):
            return True, f"You cannot use skills while {effect_name.lower()}!"

    return False, None
