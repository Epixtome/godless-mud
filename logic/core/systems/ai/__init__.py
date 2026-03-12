import random
import logging
from models import Monster
from utilities.colors import Colors
from logic.engines import vision_engine
from logic.engines.blessings_engine import Auditor
from logic.core import event_engine

logger = logging.getLogger("GodlessMUD")

def on_room_combat_tick(ctx):
    room, game = ctx.get('room'), ctx.get('game')
    if not room or not getattr(room, 'players', None):
        return

    for mob in room.monsters:
        if mob.fighting: continue
        target = None
        shout_key = None
        
        # 1. Behavior: Gatekeeper (Reputation Based)
        if "gatekeeper" in mob.tags:
            for p in room.players:
                if getattr(p, 'godmode', False): continue
                if not vision_engine.can_see(mob, p): continue
                if p.reputation < -10:
                    target = p
                    shout_key = "aggro"
                    break
        
        # 2. Behavior: Aggressive (Sight Based)
        elif "aggressive" in mob.tags:
            targets = [p for p in room.players if not getattr(p, 'godmode', False) and vision_engine.can_see(mob, p)]
            if targets:
                target = random.choice(targets)
                shout_key = "aggro"
            
        if target and target.hp > 0:
            mob.fighting = target
            target.fighting = mob
            target.state = "combat"
            if mob not in target.attackers:
                target.attackers.append(mob)
            
            # [V5.5] Dynamic Shouts from JSON
            shouts = getattr(mob, 'shouts', {})
            if shout_key and shouts.get(shout_key):
                msg = random.choice(shouts[shout_key])
                room.broadcast(f"{Colors.BOLD}{Colors.YELLOW}{mob.name} shouts: '{msg}'{Colors.RESET}")
            else:
                # Fallback
                room.broadcast(f"{Colors.RED}{mob.name} attacks {target.name}!{Colors.RESET}")

def on_combat_turn_start(ctx):
    combatant = ctx.get('entity')
    if not isinstance(combatant, Monster):
        return

    # Update tactics
    target = combatant.fighting
    if combatant.leader and combatant.leader.room == combatant.room:
        leader_target = combatant.leader.fighting
        if leader_target and leader_target != combatant and leader_target.hp > 0:
            if not target or target.hp <= 0:
                combatant.fighting = leader_target
                if combatant not in leader_target.attackers:
                    leader_target.attackers.append(combatant)
                target = leader_target

    if target and target.hp > 0:
        if combatant not in target.attackers:
            target.attackers.append(combatant)
        if not target.fighting or target.fighting.hp <= 0:
            target.fighting = combatant
            if hasattr(target, 'state') and target.state == "normal":
                target.state = "combat"


def get_mob_skill(mob, game):
    """
    Determines which skill a mob should use.
    Uses the Archetype Decision Engine for tactical evaluation.
    """
    if not isinstance(mob, Monster) or not getattr(mob, 'skills', []):
        return None

    target = mob.fighting
    if not target:
        return None

    # Use the Tactical Decision Engine
    from . import decision_engine
    return decision_engine.evaluate_tactics(mob, target, game)

def _can_afford(mob, skill):
    costs = Auditor.calculate_costs(skill, mob)
    for res, cost in costs.items():
        if mob.resources.get(res, 0) < cost: return False
    return True

def mob_ai(game):
    """Periodic tick for general AI."""
    pass

event_engine.subscribe("room_combat_tick", on_room_combat_tick)
event_engine.subscribe("combat_turn_start", on_combat_turn_start)
