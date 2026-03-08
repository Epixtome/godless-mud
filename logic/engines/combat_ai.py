"""
Handles Artificial Intelligence for combat entities (Mobs).
Includes Aggro scanning, tactical targeting (Companions), and Skill selection.
"""
import random
import logging
from models import Monster
from utilities.colors import Colors
from logic.engines import vision_engine
from logic.engines.blessings_engine import Auditor

logger = logging.getLogger("GodlessMUD")

def check_aggro(room):
    """
    Checks if any mobs in the room should initiate combat.
    Handles 'aggressive' and 'gatekeeper' tags.
    """
    if not room.players:
        return

    for mob in room.monsters:
        if mob.fighting:
            continue
            
        target = None
        
        # 1. Gatekeeper Logic (Attacks Criminals)
        if "gatekeeper" in mob.tags:
            for p in room.players:
                if getattr(p, 'godmode', False): continue
                if not vision_engine.can_see(mob, p): continue
                if p.reputation < -10: # Criminal Threshold
                    target = p
                    room.broadcast(f"{Colors.BOLD}{Colors.YELLOW}{mob.name} shouts: 'Halt, criminal!'{Colors.RESET}")
                    break
        
        # 2. Aggressive Logic (Attacks Random)
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

def update_mob_tactics(mob):
    """
    Updates mob targeting logic (Companion assist, Sticky combat).
    Modifies mob.fighting and target.attackers in place.
    """
    if not isinstance(mob, Monster):
        return

    target = mob.fighting

    # Companion Logic
    if mob.leader and mob.leader.room == mob.room:
        leader_target = mob.leader.fighting
        if leader_target and leader_target != mob and leader_target.hp > 0:
            if not target or target.hp <= 0:
                mob.fighting = leader_target
                if mob not in leader_target.attackers:
                    leader_target.attackers.append(mob)
                target = leader_target # Update local target ref

    # Ensure target knows we are fighting them (Sticky Combat)
    if target:
        if mob not in target.attackers:
            target.attackers.append(mob)
        if not target.fighting or target.fighting.hp <= 0:
            target.fighting = mob
            # Only switch to combat state if currently normal (don't interrupt casting/stunned)
            if hasattr(target, 'state') and target.state == "normal":
                target.state = "combat"

def select_mob_skill(mob, game):
    """
    Determines if a mob should use a skill this turn.
    Returns the skill object (Blessing) or None.
    """
    if not isinstance(mob, Monster) or not hasattr(mob, 'skills') or not mob.skills:
        return None

    # Class-Based Tactical Logic (GCA AI)
    if mob.active_class:
        skill_id = None
        
        if mob.active_class == 'knight':
            # Knight Tactics: Brace when low, Bash when safe
            if mob.hp < (mob.max_hp * 0.4) and "brace" in mob.skills:
                skill_id = "brace"
            elif "shield_bash" in mob.skills and random.random() < 0.3:
                skill_id = "shield_bash"
                
        elif mob.active_class == 'monk':
            # Monk Tactics: Build Flow -> Finisher
            flow = mob.ext_state.get('monk', {}).get('flow_pips', 0)
            if flow >= 10 and "dragon_strike" in mob.skills:
                skill_id = "dragon_strike"
            elif flow >= 5 and "iron_palm" in mob.skills and random.random() < 0.5:
                skill_id = "iron_palm"
            else:
                # Filter for strikes
                strikes = [s for s in mob.skills if s in ["triple_kick", "kick", "palm_strike"]]
                if strikes:
                    skill_id = random.choice(strikes)

        if skill_id:
            skill = game.world.blessings.get(skill_id)
            if skill and _can_afford(mob, skill):
                return skill

    # Default 20% Chance for general skills
    if random.random() < 0.20:
        # Pick a random skill
        skill_id = random.choice(mob.skills)
        skill = game.world.blessings.get(skill_id)
        if skill and _can_afford(mob, skill):
            return skill
            
    return None

def _can_afford(mob, skill):
    """Internal helper to check resource costs."""
    costs = Auditor.calculate_costs(skill, mob)
    for res, cost in costs.items():
        if mob.resources.get(res, 0) < cost:
            return False
    return True
