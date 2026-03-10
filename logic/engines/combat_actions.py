"""
Handles the execution of combat actions (Attacks, Skills).
Separates the 'How' of combat from the 'When' of the processor loop.
"""
import logging
import time
from models import Player, Monster
from utilities.colors import Colors
from logic.constants import Tags
from logic.core import event_engine, effects, resources, combat
from logic.engines import (
    synergy_engine, 
    blessings_engine
)
from utilities import telemetry, combat_formatter
from logic import calibration

logger = logging.getLogger("GodlessMUD")

def execute_attack(attacker, target, room, game, players_to_prompt, blessing=None, context_prefix=None):
    """
    Performs a single attack action (Auto-attack or Skill).
    Coordination point for sharded combat sub-systems.
    """
    if target == attacker: return

    # 1. Physics & Pacing Gates
    if effects.has_effect(attacker, "stalled"): return
    if "training_dummy" in getattr(attacker, 'tags', []): return

    if getattr(attacker, 'is_player', False) and not blessing:
        can_pace, _ = blessings_engine.check_pacing(attacker, weight=0.5, limit=5.0)
        if not can_pace: return

    if hasattr(attacker, 'last_attack_time'):
        attacker.last_attack_time = time.time()

    # 2. Tag Resolution
    attack_tags = combat.resolve_attack_tags(attacker, blessing)
        
    # 3. Stealth Processing
    is_backstab = False
    if "concealed" in getattr(attacker, 'status_effects', {}):
        is_backstab = True
        effects.remove_effect(attacker, "concealed")
        if hasattr(attacker, 'send_line'):
            attacker.send_line(f"{Colors.YELLOW}You strike from the shadows! (Backstab){Colors.RESET}")

    # 4. Damage Calculation
    damage = 0
    raw_damage = combat.calculate_base_damage(attacker, target, blessing)
    
    if is_backstab:
        raw_damage = int(raw_damage * 3.0)

    # 5. Defense & Mitigation (Unified)
    # Dodge Check
    dodge_ctx = {'attacker': attacker, 'target': target, 'dodged': False}
    event_engine.dispatch("combat_check_dodge", dodge_ctx)
    
    # Prone/Off-Balance Penalty (Dodge is impossible)
    if "prone" in getattr(target, 'status_effects', {}) or "off_balance" in getattr(target, 'status_effects', {}):
        dodge_ctx['dodged'] = False
        
    if dodge_ctx['dodged']:
        if hasattr(attacker, 'send_line'): attacker.send_line(f"{target.name} dodges your attack!")
        if hasattr(target, 'send_line'): target.send_line(f"You dodge {attacker.name}'s attack!")
        players_to_prompt.add(attacker)
        return

    # Mitigation (Defense Subtraction + Mitigation Events)
    defense = target.get_defense() if hasattr(target, 'get_defense') else 0
    mit_ctx = {'target': target, 'attacker': attacker, 'defense': defense, 'tags': attack_tags}
    event_engine.dispatch("on_calculate_mitigation", mit_ctx)
    
    damage = max(1, int(raw_damage - mit_ctx['defense']))
    damage = min(getattr(calibration.MaxValues, 'DAMAGE', 9999), damage)

    # Cost Processing (For Monsters or Blessing-driven attacks if not handled by Executor)
    if not getattr(attacker, 'is_player', False) and blessing:
        from logic.engines.blessings_engine import Auditor
        costs = Auditor.calculate_costs(blessing, attacker)
        for res, cost in costs.items():
            if cost > 0 and hasattr(attacker, 'resources'):
                attacker.resources[res] = max(0, attacker.resources.get(res, 0) - cost)
        if hasattr(attacker, 'room') and attacker.room:
            attacker.room.broadcast(f"{Colors.YELLOW}{attacker.name} uses {blessing.name}!{Colors.RESET}")

    # Telemetry
    telemetry.log_event(attacker, "COMBAT_DETAIL", {
        "target": target.name, "base": raw_damage, "defense": mit_ctx.get('defense', 0), "final": damage, "tags": list(attack_tags)
    })

    # 6. Critical State Modifiers
    if any(s in getattr(target, 'status_effects', {}) for s in effects.CRITICAL_STATES):
        damage = int(damage * 1.5)
        if hasattr(target, 'send_line') and damage > 0:
            target.send_line(f"{Colors.RED}You are CRITICALLY EXPOSED! (1.5x Damage){Colors.RESET}")

    # 7. Godmode Handling
    is_god = getattr(target, 'godmode', False)
    if is_god: damage = 0

    # 8. Feedback & Messaging (Sharded)
    if damage > 0 or is_god:
        att_msg, tgt_msg, room_msg = combat_formatter.format_combat_messages(attacker, target, damage, blessing, is_god)
        
        # Apply context prefix if provided (e.g., "[Extra Hit] ")
        if context_prefix:
            att_msg = f"{context_prefix}{att_msg}"
            
        combat_formatter.broadcast_combat_results(room, attacker, target, att_msg, tgt_msg, room_msg)

        # 9. Synergy & Blessing Triggers
        if getattr(attacker, 'is_player', False):
            synergy_engine.on_combat_hit(attacker, attack_tags)
            if damage > 0:
                synergy_engine.apply_combat_synergies(attacker, target, blessing, attack_tags, damage)
        
        if blessing:
            blessings_engine.apply_on_hit(attacker, target, blessing)

        # 10. Secondary Effects (Bleed, Retaliation)
        if getattr(attacker, 'is_player', False) and attacker.equipped_weapon and "bleed" in attacker.equipped_weapon.flags:
             effects.apply_effect(target, "bleed", 10)
        
        if getattr(attacker, 'is_player', False):
             if hasattr(target, 'fighting') and not target.fighting:
                 target.fighting = attacker
                 if hasattr(target, 'state'): target.state = "combat"
             if hasattr(target, 'attackers') and attacker not in target.attackers:
                 target.attackers.append(attacker)

    # 11. Attrition (Resource Drains)
    if damage > 0 and hasattr(target, 'resources'):
        if Tags.DISRUPTION in attack_tags:
            target.resources[Tags.CONCENTRATION] = max(0, target.resources.get(Tags.CONCENTRATION, 0) - 15)
        if Tags.CONCUSSIVE in attack_tags:
            resources.modify_resource(target, Tags.HEAT, 15, source=attacker.name)
        if "weight" in attack_tags and "off_balance" in getattr(target, 'status_effects', {}):
            effects.apply_effect(target, "prone", 3, log_event=True)

    # 12. Final HP Modification & Death
    resources.modify_resource(target, "hp", -damage, source=attacker, context="Combat Hit")
    target.last_hit_tick = game.tick_count 

    if damage > 0:
        event_engine.dispatch("on_combat_hit", {'attacker': attacker, 'target': target, 'damage': damage})
    
    event_engine.dispatch("combat_after_damage", {'attacker': attacker, 'target': target, 'damage': damage})
    
    # Death is handled by the entity's take_damage method dispatching 'on_death'

    # Prompt Updates
    for entity in [attacker, target]:
        if getattr(entity, 'is_player', False): players_to_prompt.add(entity)
