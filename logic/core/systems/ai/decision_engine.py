"""
logic/core/systems/ai/decision_engine.py
Advanced Archetype-based AI Decision Logic.
"""
import random
from logic.engines.blessings_engine import Auditor

def evaluate_tactics(mob, target, game):
    """
    Evaluates available skills and returns the best one to use this turn.
    """
    if not hasattr(mob, 'skills') or not mob.skills:
        return None
    
    candidates = []
    
    for skill_id in mob.skills:
        skill = game.world.blessings.get(skill_id)
        if not skill:
            continue
            
        if not _can_afford(mob, skill, game):
            continue
            
        score = _score_skill(mob, target, skill, game)
        if score > 0:
            candidates.append((score, skill))
            
    if not candidates:
        return None
    
    # Sort by score descending and pick the best (or weighted choice)
    candidates.sort(key=lambda x: x[0], reverse=True)
    
    # 20% chance to pick second best for variety/mistakes
    if len(candidates) > 1 and random.random() < 0.2:
        return candidates[1][1]
        
    return candidates[0][1]

def _can_afford(mob, skill, game):
    """Checks cooldowns and resource costs."""
    # Cooldown Check
    if skill.id in getattr(mob, 'cooldowns', {}):
        if game.tick_count < mob.cooldowns[skill.id]:
            return False
            
    # Resource Check
    costs = Auditor.calculate_costs(skill, mob)
    for res, cost in costs.items():
        if mob.resources.get(res, 0) < cost:
            return False
        
    return True

def _score_skill(mob, target, skill, game):
    """Provides a heuristic score (0-100+) based on JSON ai_priority_rules."""
    score = 10 # Base priority
    
    # Generic Identity Tags (Archetype base weights)
    tags = getattr(skill, 'identity_tags', [])
    if "finisher" in tags: score += 10
    if "protection" in tags: score += 5
    if "healing" in tags: score += 15

    # Process Data-Driven Rules
    rules = getattr(skill, 'ai_priority_rules', [])
    if not rules:
        return score

    for rule in rules:
        trigger = rule.get('trigger')
        bonus = rule.get('bonus', 0)
        
        if trigger == "hp_pct_below":
            threshold = rule.get('value', 0) / 100.0
            if (mob.hp / mob.max_hp) < threshold: score += bonus
            
        elif trigger == "hp_pct_above":
            threshold = rule.get('value', 0) / 100.0
            if (mob.hp / mob.max_hp) > threshold: score += bonus

        elif trigger == "target_hp_pct_below":
            threshold = rule.get('value', 0) / 100.0
            if (target.hp / target.max_hp) < threshold: score += bonus

        elif trigger == "resource_above":
            res_val = _get_nested_resource(mob, rule.get('resource'))
            if res_val > rule.get('value', 0): score += bonus

        elif trigger == "resource_below":
            res_val = _get_nested_resource(mob, rule.get('resource'))
            if res_val < rule.get('value', 0): score += bonus

        elif trigger == "has_status":
            if rule.get('status') in getattr(mob, 'status_effects', {}): score += bonus

        elif trigger == "target_has_status":
            if rule.get('status') in getattr(target, 'status_effects', {}): score += bonus

        elif trigger == "missing_status":
            if rule.get('status') not in getattr(mob, 'status_effects', {}): score += bonus

        elif trigger == "target_missing_status":
            if rule.get('status') not in getattr(target, 'status_effects', {}): score += bonus

        elif trigger == "is_not_toggled":
            # For stances: if we aren't already in this state
            if not mob.ext_state.get(skill.id): score += bonus

        # --- [V6.0] Tactical Triggers ---
        elif trigger == "hp_pct_below_flee":
             threshold = rule.get('value', 20) / 100.0
             if (mob.hp / mob.max_hp) < threshold: score += (bonus * 2) # Fleeing is high priority
             
        elif trigger == "target_is_stunned":
             if any(s in getattr(target, 'status_effects', {}) for s in ["stunned", "prone", "off_balance"]):
                 score += bonus
                 
        elif trigger == "target_is_silenced":
             if "silenced" in getattr(target, 'status_effects', {}): score += bonus

        elif trigger == "has_resource":
             res_val = _get_nested_resource(mob, rule.get('resource'))
             if res_val >= rule.get('value', 0): score += bonus

    return score

def _get_nested_resource(mob, path):
    """Helper to traverse player state for resources like 'monk.flow_pips'."""
    if not path: return 0
    if "." not in path:
        return mob.resources.get(path, 0)
        
    parts = path.split(".")
    obj = mob.ext_state
    for p in parts:
        if isinstance(obj, dict):
            obj = obj.get(p, 0)
        else:
            return 0
    return obj if isinstance(obj, (int, float)) else 0
