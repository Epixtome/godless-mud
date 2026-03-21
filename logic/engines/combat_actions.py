"""
Handles the execution of combat actions (Attacks, Skills).
Separates the 'How' of combat from the 'When' of the processor loop.
V7.2 Standard Refactor (Baking Branch).
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
    tags = getattr(attacker, 'tags', [])
    if any(t in tags for t in ["training_dummy", "training", "target"]):
        if not any(t in tags for t in ["elite", "tactical"]):
            return

    if getattr(attacker, 'is_player', False) and not blessing:
        can_pace, _ = blessings_engine.check_pacing(attacker, weight=0.5, limit=5.0)
        if not can_pace: return

    if hasattr(attacker, 'last_attack_time'):
        attacker.last_attack_time = time.time()

    # [V6.0] Handle Non-Attack Actions (Flee)
    if blessing and getattr(blessing, 'action', '') == 'flee':
        combat.flee(attacker)
        return

    # 2. Tag Resolution
    attack_tags = combat.resolve_attack_tags(attacker, blessing)
        
    # 3. Stealth/Backstab Processing (V7.2)
    is_backstab = False
    if effects.has_effect(attacker, "concealed"):
        is_backstab = True
        effects.remove_effect(attacker, "concealed")
        if hasattr(attacker, 'send_line'):
            attacker.send_line(f"{Colors.YELLOW}You strike from the shadows! (Backstab){Colors.RESET}")

    # 4. Reaction Gate (Parry/Block)
    # [V6.0] Handled by Blessings Engine (Math Bridge)
    reaction_hit, reaction_msg, reaction_mods = blessings_engine.resolve_reaction(attacker, target, attack_tags)
    if reaction_hit:
        if hasattr(target, 'send_line'): target.send_line(f"{Colors.GREEN}{reaction_msg}{Colors.RESET}")
        if hasattr(attacker, 'send_line'): attacker.send_line(f"{Colors.RED}{target.name} parries your strike!{Colors.RESET}")
        event_engine.dispatch("on_combat_miss", {'attacker': attacker, 'target': target, 'reason': 'parry', 'blessing': blessing})
        players_to_prompt.update([attacker, target])
        return

    # 5. Accuracy & Hit Determination (V7.2 Facade)
    accuracy = combat.combat_logic.calculate_accuracy(attacker)
    if not combat.calculate_hit_result(attacker, target, accuracy, attack_tags):
        if hasattr(attacker, 'send_line'): attacker.send_line(f"{target.name} dodges your attack!")
        if hasattr(target, 'send_line'): target.send_line(f"You dodge {attacker.name}'s attack!")
        event_engine.dispatch("on_combat_miss", {'attacker': attacker, 'target': target, 'reason': 'dodge', 'blessing': blessing})
        players_to_prompt.add(attacker)
        return

    # 6. Damage Calculation (V7.2 Flow)
    damage = combat.calculate_damage(attacker, victim=target, blessing=blessing)
    
    # [V4.5] Dynamic Damage Cap
    final_cap = getattr(calibration.MaxValues, 'DAMAGE', 75)
    if blessing and (blessing.tier >= 5 or "finisher" in getattr(blessing, 'identity_tags', [])):
        final_cap *= 2.0
    damage = min(final_cap, damage)

    # Cost Processing (Auditor Integration)
    if blessing:
        from logic.engines.blessings_engine import Auditor
        costs = Auditor.calculate_costs(blessing, attacker)
        for res, cost in costs.items():
            if cost > 0:
                resources.modify_resource(attacker, res, -cost, source="Skill Cost")
        
        if not getattr(attacker, 'is_player', False) and hasattr(attacker, 'room') and attacker.room:
            attacker.room.broadcast(f"{Colors.YELLOW}{attacker.name} uses {blessing.name}!{Colors.RESET}")
        
        event_engine.dispatch("on_skill_use", {
            'attacker': attacker, 'target': target, 'blessing': blessing, 'room': room
        })

    # 7. Status & Material Modifiers (V7.2 Grammar)
    max_mult = 1.0
    for eid in getattr(target, 'status_effects', {}):
        meta = effects.get_effect_metadata(eid, game)
        if isinstance(meta, dict):
            val = meta.get('damage_taken_mult', 1.0)
            max_mult = max(max_mult, float(val))
            if meta.get('guaranteed_crit_taken'):
                damage = int(damage * 1.5)
                if hasattr(attacker, 'send_line'):
                    attacker.send_line(f"{Colors.YELLOW}[CRITICAL] You exploit {target.name}'s exposure!{Colors.RESET}")

    if max_mult > 1.0:
        damage = int(damage * max_mult)

    # Gear/Synergy Logic
    gear_mult = blessings_engine.calculate_gear_damage_mult(target, attack_tags)
    if gear_mult != 1.0:
        damage = int(damage * gear_mult)

    # Handle Counter Strikes
    if reaction_mods.get('counter_strike') and not context_prefix:
        if hasattr(target, 'send_line'): target.send_line(f"{Colors.RED}Your counter-strike connects!{Colors.RESET}")
        execute_attack(target, attacker, room, game, players_to_prompt, context_prefix="[Counter] ")

    # 8. Feedback & Final HP Modification
    is_god = getattr(target, 'godmode', False)
    if is_god: damage = 0

    if damage > 0 or is_god:
        att_msg, tgt_msg, room_msg = combat_formatter.format_combat_messages(attacker, target, damage, blessing, is_god)
        if context_prefix: att_msg = f"{context_prefix}{att_msg}"
        combat_formatter.broadcast_combat_results(room, attacker, target, att_msg, tgt_msg, room_msg)

        # Triggers
        if getattr(attacker, 'is_player', False):
            synergy_engine.on_combat_hit(attacker, attack_tags)
            if damage > 0:
                synergy_engine.apply_combat_synergies(attacker, target, blessing, attack_tags, damage)
        
        blessings_engine.apply_on_hit(attacker, target, blessing)

    # Final HP Modification
    resources.modify_resource(target, "hp", -damage, source=attacker, context=f"{context_prefix or ''}Combat Hit".strip())
    target.last_hit_tick = game.tick_count 

    if damage > 0:
        event_engine.dispatch("on_combat_hit", {'attacker': attacker, 'target': target, 'damage': damage})
    
    event_engine.dispatch("combat_after_damage", {'attacker': attacker, 'target': target, 'damage': damage})
    
    # Prompt Updates
    players_to_prompt.update([e for e in [attacker, target] if getattr(e, 'is_player', False)])
