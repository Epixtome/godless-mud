"""
logic/modules/monk/monk.py
The Monk Domain: Contains all logic, events, and skills for the Monk class.
"""
from logic.actions.registry import register
from logic.core import status_effects_engine, resource_engine, event_engine
import time
from logic import common
from utilities.colors import Colors
from utilities import telemetry

# --- CONSTANTS ---
FLOW_MAX = 10

# --- HELPER FUNCTIONS ---

def consume_flow(player, amount):
    """
    Consumes Flow from the player.
    Returns True if successful, False if not enough flow.
    """
    current = player.ext_state.get('monk', {}).get('flow_pips', 0)
    if current >= amount:
        player.ext_state['monk']['flow_pips'] = current - amount
        return True
    return False

def _get_target(player, args, target=None):
    return common._get_target(player, args, target)

def _consume_resources(player, skill):
    # Assuming magic_engine is available in core, or we import it. 
    # For now, we use the standard consumption pattern.
    from logic.engines import magic_engine
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)
    magic_engine.consume_pacing(player, skill)

# --- SKILL HANDLERS ---

@register("iron_palm")
def handle_iron_palm(player, skill, args, target=None):
    """
    Iron Palm: Consumes 5 Flow to deal flat damage and stun.
    """
    target = _get_target(player, args, target)
    if not target: return None, True

    if not consume_flow(player, 5):
        player.send_line(f"{Colors.RED}You need 5 Flow to use Iron Palm!{Colors.RESET}")
        return None, True

    player.send_line(f"{Colors.YELLOW}You consume 5 Flow!{Colors.RESET}")
    player.send_line(f"{Colors.RED}IRON PALM! You strike {target.name} with shattering force!{Colors.RESET}")
    player.room.broadcast(f"{player.name} strikes {target.name} with an Iron Palm!", exclude_player=player)
    
    # Flat 20 DMG ignoring armor (True Damage via HP modification)
    # Corrected: Pass player object as source to ensure death rewards/favor
    resource_engine.modify_resource(target, "hp", -20, source=player, context="Iron Palm")
    
    # 2s Stun (1 tick)
    status_effects_engine.apply_effect(target, "stun", 1)

    _consume_resources(player, skill)
    return target, True

@register("palm_strike")
def handle_palm_strike(player, skill, args, target=None):
    """
    Palm Strike: Rapid strike that stuns for 1 tick. Low cost.
    """
    target = _get_target(player, args, target)
    if not target: return None, True

    player.send_line(f"{Colors.YELLOW}Palm Strike! You strike {target.name} with a swift palm!{Colors.RESET}")
    status_effects_engine.apply_effect(target, "stun", 1)
    
    from logic.engines import combat_processor
    combat_processor.execute_attack(player, target, player.room, player.game, set(), blessing=skill)

    _consume_resources(player, skill)
    return target, True

@register("dragon_strike")
def handle_dragon_strike(player, skill, args, target=None):
    """
    Dragon Strike: A powerful finisher that consumes all Flow.
    """
    target = _get_target(player, args, target)
    if not target: return None, True

    flow = player.ext_state.get('monk', {}).get('flow_pips', 0)
    if flow < 1:
        player.send_line(f"{Colors.RED}You need at least 1 Flow to use Dragon Strike!{Colors.RESET}")
        return None, True

    player.send_line(f"{Colors.CYAN}You focus your internal energy into a devastating Dragon Strike!{Colors.RESET}")
    player.room.broadcast(f"{player.name} unleashes a DRAGON STRIKE on {target.name}!", exclude_player=player)

    # Note: We pass skill to execute_attack so modifiers (like flow mult) are applied
    from logic.engines import combat_processor
    combat_processor.execute_attack(player, target, player.room, player.game, set(), blessing=skill)

    # Dispatch for Flow consumption
    event_engine.dispatch("on_skill_execute", {'player': player, 'skill': skill, 'target': target})

    _consume_resources(player, skill)
    return target, True

@register("triple_kick")
def handle_triple_kick(player, skill, args, target=None):
    """
    Triple Kick: Unleash three strikes.
    """
    target = _get_target(player, args, target)
    if not target: return None, True

    player.send_line(f"{Colors.CYAN}You unleash a flurry of three kicks on {target.name}!{Colors.RESET}")
    player.room.broadcast(f"{player.name} unleashs a triple kick on {target.name}!", exclude_player=player)

    from logic.engines import combat_processor
    # Hit 1
    combat_processor.execute_attack(player, target, player.room, player.game, set(), blessing=skill)
    # Hit 2
    if target.hp > 0:
        combat_processor.execute_attack(player, target, player.room, player.game, set(), blessing=skill)
    # Hit 3
    if target.hp > 0:
        combat_processor.execute_attack(player, target, player.room, player.game, set(), blessing=skill)

    # Dispatch for Flow Mastery/Daze
    event_engine.dispatch("on_skill_execute", {'player': player, 'skill': skill, 'target': target})

    _consume_resources(player, skill)
    return target, True

@register("meditate")
def handle_meditate(player, skill, args, target=None):
    """
    Meditate: Briefly become unsettled to recover stamina.
    """
    player.send_line(f"{Colors.CYAN}You take a moment to meditate, centering your chi.{Colors.RESET}")
    
    # The on_skill_execute event handles the stamina gain.
    # We just need to trigger the skill consumption.
    _consume_resources(player, skill)
    return None, False # No target, not a hostile action

# --- EVENT LISTENERS (PASSIVES) ---

def on_combat_hit(ctx):
    """
    Event Handler: Manages Monk Flow.
    Flow increases on successful hits.
    """
    attacker = ctx.get('attacker')
    
    # Class Gate
    if not attacker or getattr(attacker, 'active_class', None) != 'monk':
        return

    # Throttle: Limit Flow gain to 3 times per tick (Supports Triple Kick/Multi-hit)
    game = getattr(attacker, 'game', None)
    current_tick = game.tick_count if game else 0
    
    monk_state = attacker.ext_state.get('monk')
    if not monk_state: return
    
    if monk_state['throttle']['tick'] != current_tick:
        monk_state['throttle'] = {'tick': current_tick, 'count': 0}
        
    if monk_state['throttle']['count'] >= 3:
        return
        
    monk_state['throttle']['count'] += 1

    # Build Flow Logic
    current_flow = monk_state.get('flow_pips', 0)
    if current_flow < FLOW_MAX:
        monk_state['flow_pips'] = current_flow + 1
        
    # Stance Logic: If in Crane Stance and at Max Flow, grant [Evasive]
    if current_flow == FLOW_MAX and status_effects_engine.has_effect(attacker, 'crane_stance'):
        if not status_effects_engine.has_effect(attacker, 'evasive'):
            # Apply Evasive for 4 seconds (2 ticks)
            status_effects_engine.apply_effect(attacker, 'evasive', 4)
            attacker.send_line(f"{Colors.GREEN}Peak Flow: You are now EVASIVE!{Colors.RESET}")
            telemetry.log_event(attacker, "PEAK_FLOW", {"status": "EVASIVE_ACTIVE"})

    # Flow Mastery: Record Timestamp
    if 'flow_mastery' in attacker.known_blessings:
        monk_state['recent_hits'].append(time.time())

def on_calculate_skill_cost(ctx):
    """
    Event Handler: Implements Monk stamina discount based on Flow.
    """
    attacker = ctx.get('attacker') or ctx.get('player')
    blessing = ctx.get('blessing')
    costs = ctx.get('costs')

    # Class and Tag Gate
    if not attacker or getattr(attacker, 'active_class', None) != 'monk':
        return
        
    tags = getattr(blessing, 'identity_tags', [])

    # 1. Stance Discount (Flat -10 Stamina)
    if "stance" in tags:
        costs["stamina"] = max(0, costs["stamina"] - 10)

    # 2. Flow Discount (Martial Arts)
    if "martial" not in tags:
        return

    flow = attacker.ext_state.get('monk', {}).get('flow_pips', 0)
    if flow > 0:
        discount = flow * 2
        costs["stamina"] = max(0, costs["stamina"] - discount)

def on_calculate_base_damage(ctx):
    """
    Event Handler: Monk Damage Scaling.
    Crane Stance: +1 Unarmed Damage per 2 Flow Pips.
    """
    attacker = ctx.get('attacker') or ctx.get('player')
    if not attacker or getattr(attacker, 'active_class', None) != 'monk':
        return

    # Whitelist System: Allow unarmed scaling with knuckles/gloves
    weapon = attacker.equipped_weapon
    if weapon:
        tags = getattr(weapon, 'gear_tags', [])
        if not tags:
            tags = getattr(weapon, 'tags', [])
            
        # Only proceed if weapon is specifically designed for unarmed/monk style
        if not any(t in tags for t in ['unarmed', 'martial', 'martial_fists']):
            return

    # UNARMED VIRTUAL WEAPON: 1d8 Base (Axe Pattern)
    from utilities.utils import roll_dice
    base_roll = roll_dice("1d8")
    
    level = getattr(attacker, 'level', 1)
    martial_val = attacker.current_tags.get('martial', 0)
    
    # Base = 5 + (Level / 2)
    static_base = 5 + int(level / 2.0)
    
    # Scaling: 10% per Martial Point
    scaling_mult = 1.0 + (martial_val / 10.0)
    
    # Flow Multiplier: 5% per Flow Pip (Max 1.5x at 10 Flow)
    flow = attacker.ext_state.get('monk', {}).get('flow_pips', 0)
    flow_mult = 1.0 + (flow * 0.05)
    
    # Final Calculation
    damage = int((base_roll + static_base) * scaling_mult * flow_mult)
    
    # Crane Bonus: +0.5 per Flow
    if status_effects_engine.has_effect(attacker, 'crane_stance') or status_effects_engine.has_effect(attacker, 'crane_echo'):
        damage += int(flow / 2.0)
        
    # Weapon Bonus: If using Knuckles, add the weapon's own damage roll
    if weapon:
        # Use weapon's damage dice or default to 1d2 for basic wraps
        dice = getattr(weapon, 'damage_dice', "1d2")
        w_bonus = roll_dice(dice)
        damage += w_bonus
        attacker.send_line(f"{Colors.YELLOW}[MONK] Your {weapon.name} adds +{w_bonus} momentum!{Colors.RESET}")

    # Flow Mastery: +10% damage per hit in last 10s
    if 'flow_mastery' in attacker.known_blessings:
        now = time.time()
        monk_state = attacker.ext_state.get('monk', {})
        # Filter hits in last 10s
        hits = [t for t in monk_state.get('recent_hits', []) if now - t < 10.0]
        monk_state['recent_hits'] = hits # Prune old hits
        
        if hits:
            multiplier = 1.0 + (len(hits) * 0.10)
            damage = int(damage * multiplier)
            attacker.send_line(f"{Colors.MAGENTA}[FLOW MASTERY] {len(hits)} hits active! ({int((multiplier-1)*100)}% Bonus){Colors.RESET}")

    ctx['damage'] = max(damage, 1)

def on_take_damage(ctx):
    """
    Monk Weakness: Hard hits break the rhythm.
    If a Monk takes damage > 10% of Max HP, Flow resets to 0.
    """
    target = ctx.get('target')
    damage = ctx.get('damage', 0)

    if not target or getattr(target, 'active_class', None) != 'monk':
        return

    # Check for Flow Break
    if damage > (target.max_hp * 0.1):
        if 'monk' in target.ext_state:
            target.ext_state['monk']['flow_pips'] = 0
        target.send_line(f"{Colors.RED}Your Flow is broken!{Colors.RESET}")
        # Optionally remove Evasive if it was active
        if status_effects_engine.has_effect(target, 'evasive'):
            status_effects_engine.remove_effect(target, 'evasive')

def on_stance_change(ctx):
    """
    Event Handler: Implements the 'Flowing Form' passive.
    Grants a temporary evasion buff when switching stances.
    """
    player = ctx.get('player')
    
    # Class Gate
    if not player or getattr(player, 'active_class', None) != 'monk':
        return

    # Apply Evasive buff
    status_effects_engine.apply_effect(player, "evasive_step", 4) # 2 ticks
    player.send_line(f"{Colors.MAGENTA}[FLOW] Your form shifts like water! (Evasion Up){Colors.RESET}")

def on_status_removed(ctx):
    """
    Event Handler: Stance Echoes.
    When a stance drops, a lingering echo remains for 2.0s (1 tick).
    """
    player = ctx.get('player')
    status_id = ctx.get('status_id')
    
    if not player or getattr(player, 'active_class', None) != 'monk':
        return

    if status_id == "crane_stance":
        status_effects_engine.apply_effect(player, "crane_echo", 2, verbose=False, log_event=False)
        player.send_line(f"{Colors.CYAN}The Crane's power echoes in your movements...{Colors.RESET}")
    elif status_id == "turtle_stance":
        status_effects_engine.apply_effect(player, "turtle_echo", 2, verbose=False, log_event=False)
        player.send_line(f"{Colors.GREEN}The Turtle's resilience lingers...{Colors.RESET}")

def on_calculate_damage_modifier(ctx):
    """
    Event Handler: Modifies damage based on Monk mechanics.
    """
    attacker = ctx.get('attacker') or ctx.get('player')
    blessing = ctx.get('blessing')
    
    if not attacker or getattr(attacker, 'active_class', None) != 'monk':
        return

    # Triple Kick + Turtle Stance
    if blessing.id == "triple_kick" and (status_effects_engine.has_effect(attacker, "turtle_stance") or status_effects_engine.has_effect(attacker, "turtle_echo")):
        ctx['multiplier'] = ctx.get('multiplier', 1.0) * 1.5

    # Dragon Strike Flow Scaling
    if blessing.id == "dragon_strike":
        flow = attacker.ext_state.get('monk', {}).get('flow_pips', 0)
        # 1 flow = 1x, 5 flow = 3x, 8 flow = 6x, 10 flow = 10x (Surge at the end)
        if flow <= 5:
            multiplier = 1.0 + (flow * 0.4) # 1.0 to 3.0
        elif flow <= 8:
            multiplier = 3.0 + (flow - 5) * 1.0 # 3.0 to 6.0
        else: # 9, 10
            multiplier = 6.0 + (flow - 8) * 2.0 # 6.0 to 10.0
            
        ctx['multiplier'] = ctx.get('multiplier', 1.0) * multiplier

def on_skill_execute(ctx):
    """
    Event Handler: Post-skill execution logic.
    """
    player = ctx.get('player')
    skill = ctx.get('skill')
    
    if not player or getattr(player, 'active_class', None) != 'monk':
        return

    if skill.id == "dragon_strike":
        if 'monk' in player.ext_state:
            player.ext_state['monk']['flow_pips'] = 0
        player.send_line(f"{Colors.YELLOW}Your Flow is expended!{Colors.RESET}")

    elif skill.id == "meditate":
        status_effects_engine.apply_effect(player, "unsettled", 2) # 2.0s
        resource_engine.modify_resource(player, "stamina", 40)
        player.send_line(f"{Colors.GREEN}You regain stamina.{Colors.RESET}")

    elif skill.id == "triple_kick":
        # Flow Mastery: If at Max Flow (10), Triple Kick dazes the target
        flow = player.ext_state.get('monk', {}).get('flow_pips', 0)
        target = ctx.get('target')
        if flow >= 10 and target:
            status_effects_engine.apply_effect(target, "dazed", 2) # 2.0s
            player.send_line(f"{Colors.MAGENTA}*** FLOW MASTERY: {target.name} is DAZED! ***{Colors.RESET}")

def on_check_requirements(ctx):
    """
    Event Handler: Flow-Kick Logic.
    Allows Triple Kick to bypass stamina check by consuming Flow.
    """
    player = ctx.get('player')
    blessing = ctx.get('blessing')
    costs = ctx.get('costs')
    command = ctx.get('command')

    if blessing.id == 'triple_kick' and command:
        stamina_cost = costs.get('stamina', 0)
        current_stamina = player.resources.get('stamina', 0)
        
        monk_state = player.ext_state.get('monk', {})
        
        if current_stamina < stamina_cost and monk_state.get('flow_pips', 0) >= 1:
            monk_state['flow_pips'] -= 1
            costs['stamina'] = 0 # Waive cost for the check
            player.send_line(f"{Colors.MAGENTA}[FLOW] You burn Flow to force the kick!{Colors.RESET}")

def on_build_prompt(ctx):
    """
    Event Handler: Injects Monk UI into the prompt.
    """
    player = ctx.get('player')
    prompts = ctx.get('prompts')
    
    if getattr(player, 'active_class', None) == 'monk':
        monk_state = player.ext_state.get('monk', {})
        flow = monk_state.get('flow_pips', 0)
        stance = (monk_state.get('stance') or 'None').title()
        prompts.append(f"{Colors.CYAN}FLW: {flow}/10{Colors.RESET}")
        prompts.append(f"[{stance}]")

# Subscribe to global engine events
event_engine.subscribe("on_combat_hit", on_combat_hit)
event_engine.subscribe("on_take_damage", on_take_damage)
event_engine.subscribe("on_stance_change", on_stance_change)
event_engine.subscribe("on_calculate_skill_cost", on_calculate_skill_cost)
event_engine.subscribe("calculate_base_damage", on_calculate_base_damage)
event_engine.subscribe("on_status_removed", on_status_removed)
event_engine.subscribe("calculate_damage_modifier", on_calculate_damage_modifier)
event_engine.subscribe("on_skill_execute", on_skill_execute)
event_engine.subscribe("on_check_requirements", on_check_requirements)
event_engine.subscribe("on_build_prompt", on_build_prompt)
