"""
logic/modules/defiler/events.py
Defiler Event Listeners: Vile Exchange and UI.
"""
from logic.core import event_engine, resources
from utilities.colors import Colors

def register_events():
    event_engine.subscribe("on_combat_hit", on_combat_hit)
    event_engine.subscribe("on_build_prompt", on_build_prompt)

def on_combat_hit(ctx):
    """Defiler Passive: Vile Exchange. Minor life leech on every hit."""
    attacker = ctx.get('attacker')
    damage = ctx.get('damage', 0)
    
    if not attacker or getattr(attacker, 'active_class', None) != 'defiler':
        return
        
    if damage > 0:
        leech = max(1, damage // 10)
        resources.modify_resource(attacker, 'hp', leech, source="Vile Exchange", context="Leech")

def on_build_prompt(ctx):
    """Injects [WELL] display for Defilers."""
    player = ctx.get('player')
    prompts = ctx.get('prompts')
    
    if getattr(player, 'active_class', None) == 'defiler':
        well = player.ext_state.get('defiler', {}).get('blood_well', 0)
        if well > 0:
            prompts.append(f"{Colors.RED}WELL: {well}{Colors.RESET}")
