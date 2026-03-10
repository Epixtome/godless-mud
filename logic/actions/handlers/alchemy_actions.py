"""
logic/actions/handlers/alchemy_actions.py
Skills related to Alchemy: Flasks, Transmutation, and Infusions.
"""
from logic.actions.registry import register
from logic.engines import blessings_engine
from logic.core import effects
from logic.common import find_by_index
from logic.actions.skill_utils import _apply_damage
from utilities.colors import Colors

def _consume(player, skill):
    from logic.engines import magic_engine
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)
    magic_engine.consume_pacing(player, skill)

@register("flask_toss", "alchemy")
def handle_flask_toss(player, skill, args, target=None):
    player.send_line(f"You hurl {skill.name}!")
    player.room.broadcast(f"{player.name} hurls a flask!", exclude_player=player)
    
    power = blessings_engine.MathBridge.calculate_power(skill, player)
    targets = [m for m in player.room.monsters] + [p for p in player.room.players if p != player]
    
    for t in targets:
        _apply_damage(player, t, power, skill.name)

    _consume(player, skill)
    return None, True

@register("transmute")
def handle_transmute(player, skill, args, target=None):
    if not args:
        player.send_line("Transmute what?")
        return None, True
        
    item = find_by_index(player.inventory, args)
    if not item:
        player.send_line("You aren't carrying that.")
        return None, True
        
    value = item.value
    if value <= 0:
        player.send_line(f"You cannot transmute {item.name}, it has no value.")
        return None, True
        
    multiplier = 1.5 if getattr(player, 'active_class', None) == 'alchemist' else 1.0
    gold_gain = int(value * multiplier)
    
    player.inventory.remove(item)
    player.gold += gold_gain
    
    player.send_line(f"{Colors.YELLOW}You transmute {item.name} into {gold_gain} gold!{Colors.RESET}")
    _consume(player, skill)
    return None, True

@register("philosophers_stone")
def handle_philosophers_stone(player, skill, args, target=None):
    player.send_line(f"{Colors.YELLOW}You invoke the power of the Philosopher's Stone!{Colors.RESET}")
    player.room.broadcast(f"{player.name} glows with a blinding golden light!", exclude_player=player)
    
    from logic.core import resources
    if player.hp < player.max_hp:
        resources.modify_resource(player, "hp", player.max_hp - player.hp, source="Philosopher's Stone")
    if hasattr(player, 'resources'):
        resources.modify_resource(player, "stamina", 100, source="Philosopher's Stone")
        resources.modify_resource(player, "concentration", 100, source="Philosopher's Stone")
    
    _consume(player, skill)
    return None, True

@register("weapon_oil", "infuse_gear")
def handle_gear_buffs(player, skill, args, target=None):
    if skill.id == "weapon_oil" and not player.equipped_weapon:
        player.send_line("You need a weapon equipped.")
        return None, True
    if skill.id == "infuse_gear" and not player.equipped_armor:
        player.send_line("You need armor equipped.")
        return None, True
        
    effects.apply_effect(player, skill.id, 60, verbose=False)
    player.send_line(f"{Colors.CYAN}You apply {skill.name} to your gear.{Colors.RESET}")
    _consume(player, skill)
    return None, True
