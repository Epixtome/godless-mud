import random
from utilities.colors import Colors
from models import Player
from logic.actions import skill_utils
from logic.core import effects

def trap_trigger(ctx):
    # [BUG FIX] Accept both 'player' (player movement) and 'entity' (push/drag events)
    player = ctx.get('player') or ctx.get('entity')
    room = ctx.get('room')
    
    if not player or not room: return

    # trap_sense is a player-only perk; monsters skip straight to trap check
    if isinstance(player, Player) and "trap_sense" in getattr(player, 'status_effects', {}):
        traps = [i for i in room.items if "trap" in getattr(i, 'flags', [])]
        if traps:
            player.send_line(f"{Colors.YELLOW}Your trap sense warns you of traps here!{Colors.RESET}")
        return

    for item in list(room.items):
        if "trap" in getattr(item, 'flags', []):
            _trigger_trap(player, room, item)

def _trigger_trap(victim, room, trap):
    t_type = trap.metadata.get("type")
    if hasattr(victim, 'send_line'):
        victim.send_line(f"{Colors.RED}You trigger a {t_type} trap!{Colors.RESET}")
    room.broadcast(f"{victim.name} triggers a {t_type} trap!", exclude_player=victim)
    
    if t_type == "net":
        effects.apply_effect(victim, "net", 10)
        if hasattr(victim, 'send_line'):
            victim.send_line(f"{Colors.RED}You are entangled in a net! Use 'struggle' to break free.{Colors.RESET}")
    elif t_type == "fire":
        targets = [p for p in room.players] + [m for m in room.monsters]
        for t in targets:
            skill_utils._apply_damage(None, t, 30, "Fire Trap")
    elif t_type == "stamina":
        if hasattr(victim, 'resources'):
            victim.resources['stamina'] = max(0, victim.resources.get('stamina', 0) - 50)
        if hasattr(victim, 'send_line'):
            victim.send_line(f"{Colors.RED}You feel your energy instantly drained!{Colors.RESET}")

    if trap in room.items:
        room.items.remove(trap)

def chronomancer_cooldown_reduction(ctx):
    player = ctx.get('player')
    if getattr(player, 'active_class', None) == 'temporalist':
        ctx['cooldown'] = int(ctx.get('cooldown', 0) * 0.80)
