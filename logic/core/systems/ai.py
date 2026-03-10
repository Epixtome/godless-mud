import random
import logging
from models import Monster
from utilities.colors import Colors
from logic.engines import vision_engine
from logic.engines.blessings_engine import Auditor
from logic.core import event_engine

logger = logging.getLogger("GodlessMUD")

def on_room_combat_tick(ctx):
    room = ctx.get('room')
    if not room or not getattr(room, 'players', None):
        return

    for mob in room.monsters:
        if mob.fighting: continue
        target = None
        
        if "gatekeeper" in mob.tags:
            for p in room.players:
                if getattr(p, 'godmode', False): continue
                if not vision_engine.can_see(mob, p): continue
                if p.reputation < -10:
                    target = p
                    room.broadcast(f"{Colors.BOLD}{Colors.YELLOW}{mob.name} shouts: 'Halt, criminal!'{Colors.RESET}")
                    break
        elif "aggressive" in mob.tags:
            targets = [p for p in room.players if not getattr(p, 'godmode', False) and vision_engine.can_see(mob, p)]
            if targets:
                target = random.choice(targets)
            
        if target and target.hp > 0:
            mob.fighting = target
            target.fighting = mob
            target.state = "combat"
            if mob not in target.attackers:
                target.attackers.append(mob)
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

    if target:
        if combatant not in target.attackers:
            target.attackers.append(combatant)
        if not target.fighting or target.fighting.hp <= 0:
            target.fighting = combatant
            if hasattr(target, 'state') and target.state == "normal":
                target.state = "combat"

def get_mob_skill(mob, game):
    if not isinstance(mob, Monster) or not getattr(mob, 'skills', []): return None

    if mob.active_class:
        skill_id = None
        if mob.active_class == 'knight':
            if mob.hp < (mob.max_hp * 0.4) and "brace" in mob.skills:
                skill_id = "brace"
            elif "shield_bash" in mob.skills and random.random() < 0.3:
                skill_id = "shield_bash"
        elif mob.active_class == 'monk':
            flow = mob.ext_state.get('monk', {}).get('flow_pips', 0)
            if flow >= 10 and "dragon_strike" in mob.skills:
                skill_id = "dragon_strike"
            elif flow >= 5 and "iron_palm" in mob.skills and random.random() < 0.5:
                skill_id = "iron_palm"
            else:
                strikes = [s for s in mob.skills if s in ["triple_kick", "kick", "palm_strike"]]
                if strikes: skill_id = random.choice(strikes)

        if skill_id:
            skill = game.world.blessings.get(skill_id)
            if skill and _can_afford(mob, skill): return skill

    if random.random() < 0.20:
        skill_id = random.choice(mob.skills)
        skill = game.world.blessings.get(skill_id)
        if skill and _can_afford(mob, skill): return skill
    return None

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
