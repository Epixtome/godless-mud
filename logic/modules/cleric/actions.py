"""
logic/modules/cleric/actions.py
Cleric Skill Handlers: Healing, Cleanse, Shield of Faith, etc.
"""
from logic.actions.registry import register
from logic.core import effects, resources, combat
from logic.engines import magic_engine, blessings_engine
from utilities.colors import Colors
from logic import common

def _consume_resources(player, skill):
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)
    magic_engine.consume_pacing(player, skill)

@register("lay_on_hands")
def handle_lay_on_hands(player, skill, args, target=None):
    """High-potency heal scaling with faith/stats."""
    target = common._get_target(player, args, player)
    if not target: return None, True
    
    power = blessings_engine.MathBridge.calculate_power(skill, player)
    
    resources.modify_resource(target, "hp", power, source=player.name, context="Lay on Hands")
    player.send_line(f"{Colors.GREEN}Your touch mends {target.name}'s wounds! (+{power} HP){Colors.RESET}")
    if target != player and hasattr(target, 'send_line'):
        target.send_line(f"{Colors.GREEN}{player.name} lays hands on you, healing your wounds!{Colors.RESET}")
    
    _consume_resources(player, skill)
    return target, True

@register("cleanse")
def handle_cleanse(player, skill, args, target=None):
    """Removes debilitating status effects."""
    target = common._get_target(player, args, target)
    if not target: return None, True
    
    cleansed = []
    # List of "cleansable" effects (toxins, plagues, etc)
    TO_CLEANSE = ["poison", "plague", "bleed", "dazed", "curse", "blind", "silence", "slow", "weakness", "root"]
    for effect in TO_CLEANSE:
        if effects.has_effect(target, effect):
            effects.remove_effect(target, effect)
            cleansed.append(effect)
            
    if cleansed:
        player.send_line(f"{Colors.CYAN}You cleanse {target.name} of: {', '.join(cleansed)}.{Colors.RESET}")
        if target != player and hasattr(target, 'send_line'):
            target.send_line(f"{Colors.CYAN}{player.name} has cleansed your afflictions!{Colors.RESET}")
    else:
        player.send_line(f"{target.name} has no afflictions to cleanse.")
    
    _consume_resources(player, skill)
    return target, True

@register("shield_of_faith")
def handle_shield_of_faith(player, skill, args, target=None):
    target = common._get_target(player, args, player, "Cast Shield of Faith on whom?")
    if not target: return None, True
    
    effects.apply_effect(target, "shield_of_faith", 60)
    player.send_line(f"{Colors.YELLOW}You place a shimmering ward of faith upon {target.name}.{Colors.RESET}")
    if target != player and hasattr(target, 'send_line'):
        target.send_line(f"{Colors.YELLOW}{player.name} shields you with divine light!{Colors.RESET}")
        
    _consume_resources(player, skill)
    return target, True

@register("sanctify")
def handle_sanctify(player, skill, args, target=None):
    """Sanctifies the ground, buffing all allies in the room."""
    player.send_line(f"{Colors.YELLOW}You sanctify the ground beneath your feet!{Colors.RESET}")
    player.room.broadcast(f"{player.name} sanctifies the area, bathing it in holy light!", exclude_player=player)
    
    # Party-wide Buff (Players + Minions)
    allies = [p for p in player.room.players] + [m for m in player.room.monsters if getattr(m, 'leader', None) == player]
    
    for ally in allies:
        effects.apply_effect(ally, "sanctified", 30)
        if hasattr(ally, 'send_line'):
            ally.send_line(f"{Colors.YELLOW}You feel protected by the holy ground.{Colors.RESET}")
            
    _consume_resources(player, skill)
    return None, True

@register("divine_wrath")
def handle_divine_wrath(player, skill, args, target=None):
    """AOE Holy Damage to all enemies."""
    player.send_line(f"{Colors.YELLOW}You call down the wrath of the heavens!{Colors.RESET}")
    player.room.broadcast(f"{Colors.YELLOW}A pillar of holy fire descends from the sky!{Colors.RESET}", exclude_player=player)
    
    # Hostile Targeting
    targets = [m for m in player.room.monsters if getattr(m, 'leader', None) != player]
    targets += [p for p in player.room.players if p != player]
    
    for t in targets:
        # Use combat facade
        combat.handle_attack(player, t, player.room, player.game, blessing=skill)
        
    _consume_resources(player, skill)
    return None, True

@register("refresh")
def handle_refresh(player, skill, args, target=None):
    """Restore stamina to an ally (Defaults to self)."""
    target = common._get_target(player, args, player)
    if not target: return None, True
    
    amount = 20 # Standard restoration
    if target == player:
        player.send_line("You cannot refresh yourself.")
        return None, True
        
    resources.modify_resource(target, "stamina", amount, source=player.name, context="Refresh")
    player.send_line(f"{Colors.CYAN}You restore {amount} Stamina to {target.name}.{Colors.RESET}")
    if target != player and hasattr(target, 'send_line'):
        target.send_line(f"{Colors.CYAN}{player.name} refreshes your spirit! (+{amount} Stamina){Colors.RESET}")
        
    _consume_resources(player, skill)
    return target, True
