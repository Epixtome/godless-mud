"""
logic/modules/mage/events.py
Mage Event Listeners: Mana Shielding and UI.
"""
from logic.core import event_engine, effects, resources
from utilities.colors import Colors

def register_events():
    event_engine.subscribe("on_build_prompt", on_build_prompt)
    event_engine.subscribe("on_take_damage", on_take_damage)

def on_build_prompt(ctx):
    """Injects [MANA] display for Mages."""
    player = ctx.get('player')
    prompts = ctx.get('prompts')
    
    if getattr(player, 'active_class', None) == 'mage':
        conc = player.resources.get('concentration', 0)
        max_conc = player.get_max_resource('concentration')
        # Display as MANA for flavor
        prompts.append(f"{Colors.LIGHT_CYAN}Concentration: {conc}/{max_conc}{Colors.RESET}")

def on_take_damage(ctx):
    """
    Magic Shield Mechanic: 
    Redirects 50% damage to 'concentration' if shield is active.
    """
    player = ctx.get('target')
    damage = ctx.get('damage', 0)
    
    if not player or damage <= 0:
        return
        
    if effects.has_effect(player, 'magic_shield'):
        # Warlock Passive Compatibility: Verify if attacker is Warlock (Lore: They pierce shields)
        attacker = ctx.get('source')
        if attacker and getattr(attacker, 'active_class', None) == 'warlock':
            return
            
        shield_reduction = int(damage * 0.5)
        # Drain Concentration instead of HP via resource facade
        resources.modify_resource(player, 'concentration', -shield_reduction, source="Magic Shield", context="Absorbed")
        ctx['damage'] = damage - shield_reduction
        player.send_line(f"{Colors.BLUE}Your Magic Shield absorbs {shield_reduction} damage!{Colors.RESET}")
