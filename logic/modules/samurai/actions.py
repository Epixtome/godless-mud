"""
logic/modules/samurai/actions.py
Samurai Skill Handlers: Master of Precision and Lethality.
Pillar: One-Hit Lethality, Positioning, and Counters.
"""
from logic.actions.registry import register
from logic.core import effects, resources, combat
from logic.engines import action_manager, magic_engine
from utilities.colors import Colors
from logic import common

def _consume_resources(player, skill):
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)
    magic_engine.consume_pacing(player, skill)

@register("iaido_draw")
def handle_iaido_draw(player, skill, args, target=None):
    """Setup/Builder: Fast strike and Spirit generation."""
    target = common._get_target(player, args, target, "Draw against whom?")
    if not target: return None, True
    
    player.send_line(f"{Colors.YELLOW}You draw your blade with unreal speed!{Colors.RESET}")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    resources.modify_resource(player, "spirit", 1, source="Iaido Draw")
    
    _consume_resources(player, skill)
    return target, True

@register("meditative_stance")
def handle_meditative_stance(player, skill, args, target=None):
    """Setup: [Focused] buff."""
    player.send_line(f"{Colors.BLUE}You breathe deeply, focusing your spirit on the next strike.{Colors.RESET}")
    effects.apply_effect(player, "focused", 2)
    _consume_resources(player, skill)
    return None, True

@register("sever_spirit")
def handle_sever_spirit(player, skill, args, target=None):
    """Setup: [Off-Balance] and [Marked]."""
    target = common._get_target(player, args, target, "Sever whose spirit?")
    if not target: return None, True
    
    player.send_line(f"{Colors.RED}You cut through {target.name}'s balance.{Colors.RESET}")
    effects.apply_effect(target, "off_balance", 4)
    effects.apply_effect(target, "marked", 4)
    _consume_resources(player, skill)
    return target, True

@register("dragons_breath")
def handle_dragons_breath(player, skill, args, target=None):
    """Payoff/Burst: bonus damage from focus."""
    target = common._get_target(player, args, target, "Exhale upon whom?")
    if not target: return None, True
    
    is_focused = effects.has_effect(player, "focused")
    if is_focused:
        player.send_line(f"{Colors.BOLD}{Colors.YELLOW}[BURST] Dragon's Breath! Your focused strike ignites!{Colors.RESET}")
        player.focus_multiplier = 1.5
        effects.remove_effect(player, "focused")
        
    try:
        combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    finally:
         if hasattr(player, 'focus_multiplier'): del player.focus_multiplier
         
    _consume_resources(player, skill)
    return target, True

@register("tsubame_gaeshi")
def handle_tsubame_gaeshi(player, skill, args, target=None):
    """Finisher: Two hits, massive vs off-balance."""
    target = common._get_target(player, args, target, "Execute the mythical counter on whom?")
    if not target: return None, True
    
    player.send_line(f"{Colors.BOLD}{Colors.WHITE}TSUBAME GAESHI! Two strikes in a single breath!{Colors.RESET}")
    # First hit
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    
    # Second hit with multiplier if off-balance
    if effects.has_effect(target, "off_balance"):
        player.tsubame_multiplier = 3.0
        player.send_line(f"{Colors.YELLOW}The mythical second strike connects perfectly!{Colors.RESET}")
        try:
             combat.handle_attack(player, target, player.room, player.game, blessing=skill)
        finally:
             if hasattr(player, 'tsubame_multiplier'): del player.tsubame_multiplier
             
    resources.modify_resource(player, "spirit", -99) # Consumes all
    _consume_resources(player, skill)
    return target, True

@register("hissatsu_chidori")
def handle_hissatsu_chidori(player, skill, args, target=None):
    """Defense/Counter: Automatic retaliation."""
    player.send_line(f"{Colors.MAGENTA}Thunder cracks as you enter the Hissatsu stance.{Colors.RESET}")
    effects.apply_effect(player, "counter_stance", 2)
    _consume_resources(player, skill)
    return None, True

@register("shadow_dash")
def handle_shadow_dash(player, skill, args, target=None):
    """Mobility: linear blink and blind."""
    player.send_line(f"{Colors.BLACK}You flicker into the shadows, passing through foes!{Colors.RESET}")
    # Logic in combat engine for linear blinding?
    # For now, just a position/mobility buff
    effects.apply_effect(player, "haste", 2)
    _consume_resources(player, skill)
    return None, True

@register("way_of_the_warrior")
def handle_way_of_the_warrior(player, skill, args, target=None):
    """Utility/Ultimate: Long-term martial buff."""
    player.send_line(f"{Colors.BOLD}{Colors.WHITE}You commit to the old ways. Your blade feels like an extension of your soul.{Colors.RESET}")
    effects.apply_effect(player, "warrior_focus", 20)
    resources.modify_resource(player, "stamina", 50)
    _consume_resources(player, skill)
    return None, True
