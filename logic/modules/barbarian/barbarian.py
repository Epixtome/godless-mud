"""
logic/modules/barbarian/barbarian.py
The Barbarian Domain: Momentum, Rage, and Brutality.
"""
import asyncio
from logic.core import event_engine
from logic.core import status_effects_engine
from logic.core import resource_engine
from utilities.colors import Colors
from logic.engines import combat_actions
from logic.actions.registry import register
from logic import common

def _consume_resources(player, skill):
    from logic.engines import magic_engine
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)
    magic_engine.consume_pacing(player, skill)

# --- SKILL HANDLERS ---

@register("whirlwind", "whirl")
def handle_whirlwind(player, skill, args, target=None):
    # Robust Targeting: Filter out pets/allies
    targets = [m for m in player.room.monsters if getattr(m, 'leader', None) != player]
    targets += [p for p in player.room.players if p != player]
    
    if not targets:
        player.send_line("You spin your weapon through the air, but hit nothing.")
        return None, True
        
    player.send_line(f"{Colors.RED}You spin in a deadly whirlwind!{Colors.RESET}")
    player.room.broadcast(f"{player.name} spins in a deadly whirlwind!", exclude_player=player)
    
    from logic.engines import blessings_engine
    power = blessings_engine.MathBridge.calculate_power(skill, player)
    
    # Barbarian Momentum Bonus
    barb_state = player.ext_state.get('barbarian', {})
    momentum = barb_state.get('momentum', 0)
    if momentum > 0:
        # Scale damage by momentum and reset it
        multiplier = 1.0 + (momentum * 0.20)
        power = int(power * multiplier)
        barb_state['momentum'] = 0
        player.send_line(f"{Colors.YELLOW}You expend {momentum} Momentum to empower the whirlwind!{Colors.RESET}")
        # Note: Brutalize/Extra attack logic is handled in on_combat_hit
    
    from logic.actions.skill_utils import _apply_damage
    for t in targets:
        _apply_damage(player, t, power, "Whirlwind")
        
    _consume_resources(player, skill)
    return None, True

def on_combat_hit(ctx):
    """
    Event Handler: Called when a combat hit occurs.
    Manages Momentum Pips and Brutalize trigger for Barbarians.
    """
    attacker = ctx.get('attacker')
    target = ctx.get('target')
    
    if not attacker or not target:
        return

    # Class Gate
    if getattr(attacker, 'active_class', None) != 'barbarian':
        return

    barb_state = attacker.ext_state.get('barbarian')
    if not barb_state: return

    # Recursion Guard: Do not process momentum on extra attacks
    if barb_state.get('is_extra_attack'):
        return

    # Decay Rule: Reset Momentum if no hit in 6 seconds (3 ticks)
    game = getattr(attacker, 'game', None)
    current_tick = game.tick_count if game else 0
    last_hit = barb_state.get('last_hit_tick', current_tick)
    
    if current_tick - last_hit > 3:
        barb_state['momentum'] = 0
        
    barb_state['last_hit_tick'] = current_tick

    # Gain Pip (Max 5)
    current_pips = barb_state.get('momentum', 0)
    if current_pips < 5:
        barb_state['momentum'] = current_pips + 1
        attacker.send_line(f"{Colors.YELLOW}[Momentum] {barb_state['momentum']}/5{Colors.RESET}")

    # Check for Extra Attacks (Passive Scaling)
    # 3 Pips = 1 Extra, 5 Pips = 2 Extra
    extra_hits = 0
    if current_pips >= 5:
        extra_hits = 2
    elif current_pips >= 3:
        extra_hits = 1

    if extra_hits > 0:
        asyncio.create_task(_perform_extra_attacks(attacker, target, extra_hits))

async def _perform_extra_attacks(attacker, target, count):
    """Executes rapid-fire extra attacks with a delay."""
    barb_state = attacker.ext_state.get('barbarian', {})
    
    for _ in range(count):
        await asyncio.sleep(0.05) # 50ms Inter-Command Delay
        if attacker.hp <= 0 or target.hp <= 0: break
        
        barb_state['is_extra_attack'] = True
        combat_actions.execute_attack(attacker, target, attacker.room, attacker.game, set())
        barb_state['is_extra_attack'] = False

# Subscribe to events
event_engine.subscribe("on_combat_hit", on_combat_hit)