"""
Handles the execution of combat actions (Attacks, Skills).
Separates the 'How' of combat from the 'When' of the processor loop.
"""
import logging
import time
import random
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
    # [V5.0] Stalled only blocks skills (Auditor), auto-attacks continue.
    
    # [V5.0] Training Gates: Dummies can't attack, but Elite/Tactical targets can retaliate.
    tags = getattr(attacker, 'tags', [])
    if any(t in tags for t in ["training_dummy", "training", "target"]):
        if not any(t in tags for t in ["elite", "tactical"]):
            return

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
    
    # [V6.0] Riposte Bonus (Payoff for successful parry)
    if "riposte_ready" in getattr(attacker, 'status_effects', {}):
        raw_damage = int(raw_damage * 2.5)
        effects.remove_effect(attacker, "riposte_ready")
        if hasattr(attacker, 'send_line'):
            attacker.send_line(f"{Colors.MAGENTA}[RIPOSTE] You strike while they are open!{Colors.RESET}")

    # 5. Reaction Gate (Parry/Block)
    reaction_hit, reaction_msg, reaction_mods = blessings_engine.resolve_reaction(attacker, target, attack_tags)
    if reaction_hit:
        if hasattr(target, 'send_line'): target.send_line(f"{Colors.GREEN}{reaction_msg}{Colors.RESET}")
        if hasattr(attacker, 'send_line'): attacker.send_line(f"{Colors.RED}{target.name} parries your strike!{Colors.RESET}")
        # Terminate attack early
        players_to_prompt.add(attacker)
        players_to_prompt.add(target)
        return

    # 5b. Defense & Mitigation (Unified)
    # 5b. Defense & Hit Check
    from logic.core.utils import combat_logic
    accuracy = combat_logic.calculate_accuracy(attacker)
    dodge_ctx = {'attacker': attacker, 'target': target, 'dodged': False, 'accuracy': accuracy}
    
    # AOE skills and Sure-Hit skills ignore evasion
    is_area = "aoe" in attack_tags
    if not is_area:
        event_engine.dispatch("combat_check_dodge", dodge_ctx)
    
        # Prone/Off-Balance Penalty (Dodge is impossible)
        if "prone" in getattr(target, 'status_effects', {}) or "off_balance" in getattr(target, 'status_effects', {}):
            dodge_ctx['dodged'] = False
            
        # [V6.0] Deterministic Accuracy Fail (If accuracy < 100, checking vs entropy)
        if accuracy < 100:
            if random.randint(1, 100) > accuracy:
                dodge_ctx['dodged'] = True
                if hasattr(attacker, 'send_line'): attacker.send_line(f"{Colors.YELLOW}You are too blurred to strike accurately!{Colors.RESET}")
        
    if dodge_ctx['dodged']:
        if hasattr(attacker, 'send_line'): attacker.send_line(f"{target.name} dodges your attack!")
        if hasattr(target, 'send_line'): target.send_line(f"You dodge {attacker.name}'s attack!")
        players_to_prompt.add(attacker)
        return

    # 5. Mitigation (V5.0 Percentage-based + Mitigation Events)
    damage = combat.calculate_damage(attacker, target, blessing=blessing)
    
    mit_ctx = {'target': target, 'attacker': attacker, 'damage': damage, 'tags': attack_tags}
    event_engine.dispatch("on_calculate_mitigation", mit_ctx)
    damage = mit_ctx['damage']
    
    # [V4.5] Dynamic Damage Cap: Scaled by Blessing Tier
    # Standard: 75. Finishers/T5: 150.
    final_cap = getattr(calibration.MaxValues, 'DAMAGE', 75)
    if blessing:
        if blessing.tier >= 5 or "finisher" in getattr(blessing, 'identity_tags', []):
            final_cap = final_cap * 2.0
            
    damage = min(final_cap, damage)

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

    # 6. Status-Driven Damage Modifiers (Godless Grammar)
    max_mult = 1.0
    active_effects = getattr(target, 'status_effects', {})
    for eid in active_effects:
        meta = effects.get_effect_metadata(eid, game)
        if isinstance(meta, dict):
            # Explicitly type-check to satisfy Pyrefly and ensure clean math
            val = meta.get('damage_taken_mult', 1.0)
            mult = float(val) if isinstance(val, (int, float)) else 1.0
            
            if mult > max_mult:
                max_mult = mult
            
            # [V6.0] Exposure Grammar: Guaranteed Crit
            if meta.get('guaranteed_crit_taken'):
                damage = int(damage * 1.5) # Minimum critical payoff
                if hasattr(attacker, 'send_line'):
                    attacker.send_line(f"{Colors.YELLOW}[CRITICAL] You exploit {target.name}'s exposure!{Colors.RESET}")

    if max_mult > 1.0:
        damage = int(damage * max_mult)

    # 6b. Gear/Material Modifiers (Gear Grammar)
    gear_mult = blessings_engine.calculate_gear_damage_mult(target, attack_tags)
    if gear_mult != 1.0:
        damage = int(damage * gear_mult)
        if gear_mult > 1.0 and hasattr(attacker, 'send_line'):
             attacker.send_line(f"{Colors.YELLOW}[SYNERGY] Your {list(attack_tags)[0] if attack_tags else 'attack'} resonates with {target.name}'s gear!{Colors.RESET}")

    # 7. GODMODE & REACTION RESULTS
    is_god = getattr(target, 'godmode', False)
    if is_god: damage = 0

    # Handle Counter Strikes (Barbarian Logic)
    if reaction_mods.get('counter_strike') and not context_prefix:
        if hasattr(target, 'send_line'):
             target.send_line(f"{Colors.RED}Your counter-strike connects!{Colors.RESET}")
        execute_attack(target, attacker, room, game, players_to_prompt, context_prefix="[Counter] ")

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
        
        # Centralized On-Hit (Handles both Blessing logic and Weapon flags)
        blessings_engine.apply_on_hit(attacker, target, blessing)
            
        # [V5.0] Auto-Attack Posture Logic (Redundant check removed)
        
        # [REMOVED] Reciprocal Engagement now handled by systems/engagement.py

    # 11. Attrition (Resource Drains)
    if damage > 0 and hasattr(target, 'resources'):
        # Removed redundant check_posture_break

        if Tags.DISRUPTION in attack_tags:
            target.resources[Tags.CONCENTRATION] = max(0, target.resources.get(Tags.CONCENTRATION, 0) - 15)
        if Tags.CONCUSSIVE in attack_tags:
            resources.modify_resource(target, Tags.HEAT, 15, source=attacker.name)
        if "weight" in attack_tags and "off_balance" in getattr(target, 'status_effects', {}):
            effects.apply_effect(target, "prone", 3, log_event=True)

    # 12. Final HP Modification & Death
    resources.modify_resource(target, "hp", -damage, source=attacker, context=f"{context_prefix or ''}Combat Hit".strip())
    target.last_hit_tick = game.tick_count 

    if damage > 0:
        event_engine.dispatch("on_combat_hit", {'attacker': attacker, 'target': target, 'damage': damage})
    
    event_engine.dispatch("combat_after_damage", {'attacker': attacker, 'target': target, 'damage': damage})
    
    # Death is handled by the entity's take_damage method dispatching 'on_death'

    # Prompt Updates
    for entity in [attacker, target]:
        if getattr(entity, 'is_player', False): players_to_prompt.add(entity)
