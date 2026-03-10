"""
logic/actions/handlers/utility/field_prep.py
Tactical and Medical skills: Bandage and Smoke Bomb.
"""
from logic.actions.registry import register
from logic.core import effects, resources, combat
from logic.common import _get_target
from logic.engines import action_manager
from utilities.colors import Colors

def _consume(player, skill):
    from logic.engines import magic_engine
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)
    magic_engine.consume_pacing(player, skill)

@register("bandage", "first_aid")
def handle_bandage(player, skill, args, target=None):
    target_ent = _get_target(player, args, target, "Bandage whom?")
    if not target_ent: return None, True

    player.send_line(f"You begin applying a bandage to {target_ent.name}...")

    async def _finish_bandage():
        if "bleed" in getattr(target_ent, 'status_effects', {}):
            effects.remove_effect(target_ent, "bleed")
            if hasattr(target_ent, 'send_line'):
                target_ent.send_line(f"{Colors.GREEN}The bleeding stops.{Colors.RESET}")
            
        heal_amt = 25 
        resources.modify_resource(target_ent, "hp", heal_amt, source=player, context="Bandage")
        player.send_line(f"{Colors.GREEN}You finish bandaging {target_ent.name}. (+{heal_amt} HP){Colors.RESET}")
        
    action_manager.start_action(player, 5.0, _finish_bandage, tag="bandaging", fail_msg="Bandaging interrupted.")
    _consume(player, skill)
    return None, True

@register("smoke_bomb")
def handle_smoke_bomb(player, skill, args, target=None):
    player.room.broadcast(f"{Colors.WHITE}{player.name} smashes a smoke bomb! Thick smoke fills the room!{Colors.RESET}", exclude_player=None)
    
    for entity in player.room.players + player.room.monsters:
        if entity.fighting:
            combat.stop_combat(entity)
            if hasattr(entity, 'send_line'):
                entity.send_line(f"{Colors.YELLOW}Combat is interrupted by the smoke!{Colors.RESET}")
    
    _consume(player, skill)
    return None, True
