"""
logic/modules/cleric/actions.py
Cleric Class Skills: Divine Guardian implementation.
V7.2 Standard Refactor.
"""
from logic.actions.registry import register
from logic.core import effects, resources, combat
from utilities.colors import Colors

# Internal Helper: Consume resources and set cooldowns
def _consume_resources(player, skill):
    from logic.engines import magic_engine
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)

@register("holy_strike")
def handle_holy_strike(player, skill, args, target=None):
    """Setup/Builder: Faith generator."""
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    
    player.send_line(f"{Colors.YELLOW}You strike {target.name} with a weapon bathed in holy light!{Colors.RESET}")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    
    # Generate Faith (Resource expected in URM)
    resources.modify_resource(player, 'faith', 1, source="Holy Strike")
    
    _consume_resources(player, skill)
    return target, True

@register("divine_mark")
def handle_divine_mark(player, skill, args, target=None):
    """Setup: Applies Illuminated status."""
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    
    player.send_line(f"{Colors.YELLOW}You mark {target.name} with a divine brand!{Colors.RESET}")
    effects.apply_effect(target, "illuminated", 5)
    
    _consume_resources(player, skill)
    return target, True

@register("divine_wrath")
def handle_divine_wrath(player, skill, args, target=None):
    """Payoff/AOE: Pillar of fire."""
    player.send_line(f"{Colors.BOLD}{Colors.YELLOW}DIVINE WRATH!{Colors.RESET} A pillar of holy fire descends!")
    
    targets = [m for m in player.room.monsters if combat.is_target_valid(player, m)]
    for t in targets:
        combat.handle_attack(player, t, player.room, player.game, blessing=skill)
        
    _consume_resources(player, skill)
    return None, True

@register("judgment")
def handle_judgment(player, skill, args, target=None):
    """Payoff: High damage vs Illuminated targets."""
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    
    player.send_line(f"{Colors.BOLD}{Colors.WHITE}JUDGMENT!{Colors.RESET} You call down celestial power upon the wicked!")
    
    # Logic-Data wall: grammar bonus handled in JSON, but we can add flavor
    if effects.has_effect(target, "illuminated"):
        player.send_line(f"{Colors.CYAN}The divine brand erupts in blinding light!{Colors.RESET}")
        
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    
    _consume_resources(player, skill)
    return target, True

@register("shield_of_faith")
def handle_shield_of_faith(player, skill, args, target=None):
    """Defense: Wards an ally."""
    from .utils import get_target
    target = get_target(player, args, player)
    if not target: return None, True
    
    player.send_line(f"{Colors.YELLOW}You weave a protective ward around {target.name}.{Colors.RESET}")
    effects.apply_effect(target, "shielded", 4)
    
    _consume_resources(player, skill)
    return target, True

@register("sanctify")
def handle_sanctify(player, skill, args, target=None):
    """Defense/Utility: Area aura."""
    player.send_line(f"{Colors.YELLOW}You sanctify the ground, creating a sanctuary of light.{Colors.RESET}")
    
    allies = [p for p in player.room.players]
    for a in allies:
        effects.apply_effect(a, "fortified", 6)
        a.send_line(f"{Colors.GREEN}You feel safe within the sanctuary.{Colors.RESET}")
        
    _consume_resources(player, skill)
    return None, True

@register("angelic_stride")
def handle_angelic_stride(player, skill, args, target=None):
    """Mobility: Transcend physical limits."""
    player.send_line(f"{Colors.CYAN}You glide across the battlefield, carried by unseen wings.{Colors.RESET}")
    
    # Remove movement blocks, apply haste
    for s in ["prone", "stalled", "immobilized"]:
        if effects.has_effect(player, s):
            effects.remove_effect(player, s)
            
    effects.apply_effect(player, "haste", 3)
    
    _consume_resources(player, skill)
    return None, True

@register("lay_on_hands")
def handle_lay_on_hands(player, skill, args, target=None):
    """Utility/Signature: Potent heal."""
    from .utils import get_target
    target = get_target(player, args, player)
    if not target: return None, True
    
    player.send_line(f"{Colors.GREEN}Your touch mends {target.name}'s wounds with divine warmth.{Colors.RESET}")
    
    # 30% Max HP Heal
    heal = int(target.max_hp * 0.3)
    resources.modify_resource(target, "hp", heal, source=player.name)
    
    # Also cleanse common ailments
    for e in ["poison", "bleed", "plague"]:
        if effects.has_effect(target, e):
            effects.remove_effect(target, e)
            
    _consume_resources(player, skill)
    return target, True
