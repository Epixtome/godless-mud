"""
logic/modules/cleric/cleric.py
The Cleric Domain: Healing, Restoration, and Divine Protection.
"""
from logic.actions.registry import register
from logic.core import event_engine, status_effects_engine, resource_engine
from utilities.colors import Colors
from logic import common

# --- SKILL HANDLERS ---

def _consume_resources(player, skill):
    from logic.engines import magic_engine
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)
    magic_engine.consume_pacing(player, skill)

# --- SKILL HANDLERS ---

@register("lay_on_hands")
def handle_lay_on_hands(player, skill, args, target=None):
    """High-potency heal scaling with faith/stats."""
    target = common._get_target(player, args, target)
    if not target: return None, True
    
    from logic.engines import blessings_engine
    power = blessings_engine.MathBridge.calculate_power(skill, player)
    
    resource_engine.modify_resource(target, "hp", power, source=player.name, context="Lay on Hands")
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
        if status_effects_engine.has_effect(target, effect):
            status_effects_engine.remove_effect(target, effect)
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
    
    status_effects_engine.apply_effect(target, "shield_of_faith", 60)
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
        status_effects_engine.apply_effect(ally, "sanctified", 30)
        if hasattr(ally, 'send_line'):
            ally.send_line(f"{Colors.YELLOW}You feel protected by the holy ground.{Colors.RESET}")
            
    _consume_resources(player, skill)
    return None, True

@register("divine_wrath")
def handle_divine_wrath(player, skill, args, target=None):
    """AOE Holy Damage to all enemies."""
    player.send_line(f"{Colors.YELLOW}You call down the wrath of the heavens!{Colors.RESET}")
    player.room.broadcast(f"{Colors.YELLOW}A pillar of holy fire descends from the sky!{Colors.RESET}", exclude_player=player)
    
    from logic.engines import blessings_engine
    power = blessings_engine.MathBridge.calculate_power(skill, player)
    
    # Hostile Targeting: All mobs NOT leading/following player + All other players
    # (In a real MUD we might check for 'party' or 'kingdom' flag)
    targets = [m for m in player.room.monsters if getattr(m, 'leader', None) != player]
    targets += [p for p in player.room.players if p != player]
    
    from logic.actions.skill_utils import _apply_damage
    for t in targets:
        _apply_damage(player, t, power, "Divine Wrath")
        
    _consume_resources(player, skill)
    return None, True

@register("refresh")
def handle_refresh(player, skill, args, target=None):
    """Restore stamina to an ally (Defaults to self)."""
    target = common._get_target(player, args, player) # Default to self
    if not target: return None, True
    
    amount = 30 # Standard restoration
    from logic.core import resource_engine
    resource_engine.modify_resource(target, "stamina", amount, source=player.name, context="Refresh")
    player.send_line(f"{Colors.CYAN}You restore {amount} Stamina to {target.name}.{Colors.RESET}")
    if target != player and hasattr(target, 'send_line'):
        target.send_line(f"{Colors.CYAN}{player.name} refreshes your spirit! (+{amount} Stamina){Colors.RESET}")
        
    _consume_resources(player, skill)
    return target, True

# --- EVENT LISTENERS ---

def on_build_prompt(ctx):
    """Cleric-specific prompt logic (e.g. Aura display)."""
    player = ctx.get('player')
    prompts = ctx.get('prompts')
    
    if getattr(player, 'active_class', None) == 'cleric':
        aura = player.ext_state.get('cleric', {}).get('aura')
        if aura:
            prompts.append(f"{Colors.YELLOW}[{aura.upper()}]{Colors.RESET}")

# --- REGISTRATION ---
event_engine.subscribe("on_build_prompt", on_build_prompt)
