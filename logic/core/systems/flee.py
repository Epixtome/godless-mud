"""
logic/core/systems/flee.py
Handles the logic for escaping from combat.
Part of the V7.2 Core Engine Decoupling.
"""
import random
from utilities.colors import Colors
from logic.core import event_engine, combat

def handle_flee(entity):
    """Executes a flee attempt for a player or monster."""
    room = getattr(entity, 'room', None)
    if not room: return False

    if getattr(entity, 'is_player', False):
        from logic.commands.combat_commands import flee as flee_cmd
        return flee_cmd(entity, "")
    else:
        # Simple Mob Flee
        exits = list(room.exits.keys())
        if not exits: return False
        
        direction = random.choice(exits)
        from logic.commands.movement_commands import _move
        if _move(entity, direction):
            combat.stop_combat(entity)
            event_engine.dispatch("on_flee", {'entity': entity, 'room': room, 'direction': direction})
            room.broadcast(f"{Colors.YELLOW}{entity.name} has fled {direction}!{Colors.RESET}")
            return True
    return False
