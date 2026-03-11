"""
logic/modules/barbarian/events.py
Barbarian Event Listeners: Momentum and UI.
"""
from logic.core import event_engine, effects
from logic.engines import combat_actions
from utilities.colors import Colors

def register_events():
    event_engine.subscribe("on_combat_hit", on_combat_hit)
    event_engine.subscribe("on_build_prompt", on_build_prompt)

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

    # Check for Extra Attacks (Passive Scaling)
    # 3 Pips = 1 Extra, 5 Pips = 2 Extra
    extra_hits = 0
    if current_pips >= 5:
        extra_hits = 2
    elif current_pips >= 3:
        extra_hits = 1

    if extra_hits > 0:
        _perform_extra_attacks(attacker, target, extra_hits)

def _perform_extra_attacks(attacker, target, count):
    """Executes rapid-fire extra attacks immediately within the tick."""
    barb_state = attacker.ext_state.get('barbarian', {})
    
    for _ in range(count):
        if attacker.hp <= 0 or target.hp <= 0 or getattr(target, 'pending_death', False):
            break
        
        barb_state['is_extra_attack'] = True
        # Track the extra hit by prefixing the next attack context
        combat_actions.execute_attack(attacker, target, attacker.room, attacker.game, set(), context_prefix=f"{Colors.YELLOW}[Extra Hit]{Colors.RESET} ")
        barb_state['is_extra_attack'] = False

def on_build_prompt(ctx):
    """Injects Momentum display into the prompt for Barbarians."""
    player = ctx.get('player')
    prompts = ctx.get('prompts')
    
    if getattr(player, 'active_class', None) == 'barbarian':
        momentum = player.ext_state.get('barbarian', {}).get('momentum', 0)
        if momentum > 0:
            prompts.append(f"{Colors.YELLOW}[Momentum {momentum}/5]{Colors.RESET}")
