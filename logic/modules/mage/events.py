"""
logic/modules/mage/events.py
Mage Event Listeners: Mana Shielding and UI.
V7.2 Standard Refactor (Baking Branch).
"""
from logic.core import event_engine, effects, resources
from utilities.colors import Colors

def register_events():
    event_engine.subscribe("on_build_prompt", on_build_prompt)
    event_engine.subscribe("on_take_damage", on_take_damage)

def on_build_prompt(ctx):
    """Injects [CONC] display for Mages."""
    player, prompts = ctx.get('player'), ctx.get('prompts')
    if getattr(player, 'active_class', None) == 'mage':
        conc = resources.get_resource(player, 'concentration')
        mc = player.get_max_resource('concentration')
        prompts.append(f"{Colors.LIGHT_CYAN}[CONC:{conc}/{mc}]{Colors.RESET}")

def on_take_damage(ctx):
    """
    Magic Shield Mechanic: 
    Redirects 50% damage to 'concentration' if shield is active.
    """
    target, damage = ctx.get('target'), ctx.get('damage', 0)
    if not target or damage <= 0: return
        
    if effects.has_effect(target, 'magic_shield'):
        # [V7.2] Lore check: Warlocks pierce arcane shields.
        attacker = ctx.get('source')
        if attacker and getattr(attacker, 'active_class', None) == 'warlock':
            return
            
        shield_reduction = int(damage * 0.5)
        # Drain Concentration instead of HP via resource facade (URM)
        resources.modify_resource(target, 'concentration', -shield_reduction, source="Magic Shield")
        
        ctx['damage'] = damage - shield_reduction
        if hasattr(target, 'send_line'):
            target.send_line(f"{Colors.BLUE}Your Magic Shield absorbs {shield_reduction} damage!{Colors.RESET}")
