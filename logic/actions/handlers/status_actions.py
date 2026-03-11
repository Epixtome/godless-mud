"""
logic/actions/handlers/status_actions.py
Complex status effects: Stealth, Stances, Songs, Meditation.
"""
import random
from logic.actions.registry import register
from logic.core import effects
from logic.engines import magic_engine, action_manager
from utilities.colors import Colors

def _consume(player, skill):
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)
    magic_engine.consume_pacing(player, skill)

@register("stealth", "hide")
def handle_stealth(player, skill, args, target=None):
    if player.fighting:
        player.send_line("You cannot hide while fighting! Use 'vanish' instead.")
        return None, True
        
    effects.apply_effect(player, "concealed", 10, verbose=False)
    player.send_line(f"{Colors.CYAN}You slip into the shadows.{Colors.RESET}")
    _consume(player, skill)
    return None, True

@register("vanish")
def handle_vanish(player, skill, args, target=None):
    effects.apply_effect(player, "concealed", 10, verbose=False)
    player.send_line(f"{Colors.CYAN}You throw a smoke bomb and vanish!{Colors.RESET}")
    player.room.broadcast(f"{player.name} vanishes in a puff of smoke!", exclude_player=player)
    
    player.fighting = None
    player.state = "normal"
    
    _consume(player, skill)
    return None, True

@register("meditate")
def handle_meditate(player, skill, args, target=None):
    if player.fighting:
        player.send_line("You cannot meditate during combat!")
        return None, True
        
    def _cleanup():
        effects.remove_effect(player, "meditating")
        player.send_line("You break your meditation.")

    effects.apply_effect(player, "meditating", 9999, verbose=False)
    player.send_line(f"{Colors.CYAN}You enter a deep meditative trance...{Colors.RESET}")
    
    action_manager.start_action(player, 9999.0, lambda: None, tag="meditating", on_interrupt=_cleanup)
    return None, True

@register("tiger_stance")
def handle_tiger_stance(player, skill, args, target=None):
    _clear_stances(player)
    effects.apply_effect(player, "tiger_stance", 60, verbose=False)
    player.send_line(f"{Colors.RED}You assume the Tiger Stance!{Colors.RESET}")
    _consume(player, skill)
    return None, True

@register("turtle_stance")
def handle_turtle_stance(player, skill, args, target=None):
    _clear_stances(player)
    effects.apply_effect(player, "turtle_stance", 60, verbose=False)
    player.send_line(f"{Colors.GREEN}You assume the Turtle Stance!{Colors.RESET}")
    _consume(player, skill)
    return None, True

def _clear_stances(player):
    """
    Metadata-driven stance removal.
    Clears any active status effects belonging to the 'stance' group.
    """
    to_remove = []
    for eff_id in getattr(player, 'status_effects', {}):
        # We use the effect engine facade to get definitions
        defn = effects.get_effect_definition(eff_id, player.game)
        if defn and defn.get('group') == 'stance':
            to_remove.append(eff_id)
            
    for s in to_remove:
        effects.remove_effect(player, s)

@register("quick_step", "evasive_step")
def handle_evasive_step(player, skill, args, target=None):
    effects.apply_effect(player, "evasive_step", 60, verbose=False)
    player.send_line(f"{Colors.CYAN}You shift your weight, ready to dodge incoming attacks.{Colors.RESET}")
    _consume(player, skill)
    return None, True

@register("sneak")
def handle_sneak(player, skill, args, target=None):
    effects.apply_effect(player, "sneaking", 60, verbose=False)
    player.send_line(f"{Colors.CYAN}You move with silent, calculated steps.{Colors.RESET}")
    _consume(player, skill)
    return None, True

@register("parry")
def handle_parry(player, skill, args, target=None):
    effects.apply_effect(player, "parrying", 4, verbose=False)
    player.send_line(f"{Colors.CYAN}You raise your weapon, ready to deflect the next blow.{Colors.RESET}")
    _consume(player, skill)
    return None, True

@register("mark_target", "death_mark")
def handle_mark_target(player, skill, args, target=None):
    from logic.common import _get_target
    target = _get_target(player, args, target, "Mark whom?")
    if not target: return None, True

    effects.apply_effect(target, "marked", 30)
    player.send_line(f"{Colors.RED}You mark {target.name} for death.{Colors.RESET}")
    
    _consume(player, skill)
    return target, True

@register("poison", "envenom")
def handle_poison(player, skill, args, target=None):
    weapon = getattr(player, 'equipped_weapon', None)
    if not weapon:
        player.send_line("You need a weapon equipped to apply poison.")
        return None, True
    effects.apply_effect(player, "poison_coated", 60, verbose=False)
    player.send_line(f"{Colors.GREEN}You carefully coat your {weapon.name} with deadly toxin.{Colors.RESET}")
    _consume(player, skill)
    return None, True

@register("sheathe", "iaido")
def handle_sheathe(player, skill, args, target=None):
    if player.fighting:
        player.send_line("You cannot sheathe your weapon in the heat of combat!")
        return None, True
        
    effects.apply_effect(player, "sheathed_stance", 9999, verbose=False)
    player.send_line(f"{Colors.CYAN}You sheathe your weapon, focusing your mind for a strike.{Colors.RESET}")
    _consume(player, skill)
    return None, True

@register("third_eye")
def handle_third_eye(player, skill, args, target=None):
    effects.apply_effect(player, "third_eye", 30, verbose=False)
    player.send_line(f"{Colors.CYAN}You focus your mind, opening your Third Eye.{Colors.RESET}")
    _consume(player, skill)
    return None, True

@register("shadow_step")
def handle_shadow_step(player, skill, args, target=None):
    from logic.commands import movement_commands as movement
    direction = args.lower() if args else None
    
    if direction and direction in player.room.exits:
        player.send_line(f"{Colors.CYAN}You step into the shadows and appear {direction}!{Colors.RESET}")
        movement._move(player, direction)
    else:
        player.send_line("Shadow step where?")
        
    _consume(player, skill)
    return None, True

@register("roll_dice", "dice")
def handle_roll_dice(player, skill, args, target=None):
    roll = random.randint(1, 6)
    player.send_line(f"You roll a die... it lands on {Colors.CYAN}{roll}{Colors.RESET}!")
    _consume(player, skill)
    return None, True

@register("buff", "rage", "stone_skin", "crane_stance", "defensive_stance")
def handle_generic_buffs(player, skill, args, target=None):
    effect_id = "berserk_rage" if skill.id == "rage" else skill.id
    effects.apply_effect(player, effect_id, 30, verbose=False)
    
    player.send_line(f"{Colors.GREEN}You use {skill.name}!{Colors.RESET}")
    _consume(player, skill)
    return None, True
