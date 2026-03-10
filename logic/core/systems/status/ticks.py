"""
logic/systems/status/ticks.py
Handlers for taking damage and recovering from status effects over time.
"""
from logic.core import event_engine, resources
from utilities.colors import Colors

def handle_tick_damage(ctx):
    """Processes recurring damage effects."""
    effect_id = ctx.get('effect_id')
    entity = ctx.get('entity')
    game = ctx.get('game')
    
    if effect_id in ['bleed', 'burn', 'poison']:
        damage = 0
        msg = ""
        act_msg = ""
        
        if effect_id == 'bleed':
            damage = 15
            msg = f"{Colors.RED}You bleed from your wounds. [-{damage} HP]{Colors.RESET}"
            act_msg = f"{entity.name} bleeds."
        elif effect_id == 'burn':
            damage = 25
            msg = f"{Colors.RED}Flames singe your flesh! [-{damage} HP]{Colors.RESET}"
            act_msg = f"{entity.name} burns."
        elif effect_id == 'poison':
            damage = 10
            msg = f"{Colors.GREEN}Venom courses through your veins. [-{damage} HP]{Colors.RESET}"
            act_msg = f"{entity.name} looks sickly from poison."
            
        if hasattr(entity, 'send_line'):
            entity.send_line(msg)
            
        # Apply damage
        resources.modify_resource(entity, 'hp', -damage, source="Status", context=effect_id.title())
        
        # Room broadcast
        if getattr(entity, 'room', None):
            entity.room.broadcast(act_msg, exclude_player=entity)

def register_ticks():
    event_engine.subscribe("effect_tick", handle_tick_damage)
