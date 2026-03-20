"""
logic/modules/bard/actions.py
Bard Skill Handlers: Master of Tempo and Utility.
Pillar: Disruption, Resonance, and Auras.
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

@register("discordant_note")
def handle_discordant_note(player, skill, args, target=None):
    """Setup/Builder: Sonic damage and Rhythm generation."""
    target = common._get_target(player, args, target, "Jar which ear?")
    if not target: return None, True
    
    player.send_line(f"{Colors.BLUE}You strike a jarring chord that resonates within {target.name}!{Colors.RESET}")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    resources.modify_resource(player, "rhythm", 5, source="Discordant Note")
    
    _consume_resources(player, skill)
    return target, True

@register("fascinate")
def handle_fascinate(player, skill, args, target=None):
    """Setup: [Dazed] applier."""
    target = common._get_target(player, args, target, "Fascinate whom?")
    if not target: return None, True
    
    player.send_line(f"{Colors.CYAN}You weave a hypnotic melody that captivates {target.name}.{Colors.RESET}")
    effects.apply_effect(target, "dazed", 4)
    _consume_resources(player, skill)
    return target, True

@register("echoing_verse")
def handle_echoing_verse(player, skill, args, target=None):
    """Setup: [Marked] for sonic amplification."""
    target = common._get_target(player, args, target, "Mark whose soul?")
    if not target: return None, True
    
    player.send_line(f"{Colors.YELLOW}You mark the resonance of {target.name}'s spirit.{Colors.RESET}")
    effects.apply_effect(target, "marked", 8)
    _consume_resources(player, skill)
    return target, True

@register("crescendo")
def handle_crescendo(player, skill, args, target=None):
    """Payoff/Finisher: massive burst vs Dazed."""
    target = common._get_target(player, args, target, "Unleash the peak upon whom?")
    if not target: return None, True
    
    if effects.has_effect(target, "dazed"):
        player.send_line(f"{Colors.BOLD}{Colors.WHITE}CRESCENDO! The world shatters around {target.name}!{Colors.RESET}")
        player.crescendo_multiplier = 3.0
        try:
            combat.handle_attack(player, target, player.room, player.game, blessing=skill)
        finally:
             if hasattr(player, 'crescendo_multiplier'): del player.crescendo_multiplier
             effects.remove_effect(target, "dazed")
    else:
        player.send_line(f"Your performance peaks, but {target.name} isn't properly fascinated.")
        combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    
    _consume_resources(player, skill)
    return target, True

@register("soul_requiem")
def handle_soul_requiem(player, skill, args, target=None):
    """Payoff/AOE: Sonic detonation of Marked targets + Team Heal."""
    player.send_line(f"{Colors.BOLD}{Colors.MAGENTA}SOUL REQUIEM! A mournful dirge echoes...{Colors.RESET}")
    targets = [m for m in player.room.monsters if effects.has_effect(m, "marked")]
    for t in targets:
        combat.handle_attack(player, t, player.room, player.game, blessing=skill)
        
    # Team Heal
    for p in player.room.players:
        heal_amt = int(p.max_hp * 0.1)
        p.modify_hp(heal_amt)
        p.send_line(f"{Colors.GREEN}The requiem heals you for {heal_amt} health.{Colors.RESET}")
        
    _consume_resources(player, skill)
    return None, True

@register("serenade_of_safety")
def handle_serenade_of_safety(player, skill, args, target=None):
    """Defense: AOE Shielding."""
    player.send_line(f"{Colors.CYAN}A protective lullaby surrounds your party.{Colors.RESET}")
    for p in player.room.players:
        effects.apply_effect(p, "shielded", 4)
        effects.apply_effect(p, "braced", 4)
        
    _consume_resources(player, skill)
    return None, True

@register("allegro_step")
def handle_allegro_step(player, skill, args, target=None):
    """Mobility: Warp and Haste."""
    player.send_line(f"{Colors.WHITE}Allegro! You dash forward with supernatural speed.{Colors.RESET}")
    effects.apply_effect(player, "haste", 2)
    if effects.has_effect(player, "slowed"):
        effects.remove_effect(player, "slowed")
        
    _consume_resources(player, skill)
    return None, True

@register("hymn_of_regeneration")
def handle_hymn_of_regeneration(player, skill, args, target=None):
    """Utility/Aura: Persistent HoT."""
    player.send_line(f"{Colors.GREEN}You begin an ancient hymn of natural mending.{Colors.RESET}")
    rhythm = player.ext_state.get('bard', {}).get('rhythm', 0)
    # Scales duration or potency by rhythm?
    duration = 10 + (rhythm // 10)
    for p in player.room.players:
        effects.apply_effect(p, "regeneration", duration)
        
    resources.modify_resource(player, "rhythm", -rhythm)
    _consume_resources(player, skill)
    return None, True
