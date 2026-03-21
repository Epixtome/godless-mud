"""
logic/modules/archer/actions.py
Archer Skill Handlers: Master of Reach and Tracking.
V7.2 Standard Refactor (Baking Branch).
"""
from logic.actions.registry import register
from logic.core import effects, resources, combat, perception
from logic.engines import magic_engine
from utilities.colors import Colors
from logic import common

def _consume_resources(player, skill):
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)
    magic_engine.consume_pacing(player, skill)

def _ridge_check(player, target, skill_name):
    """
    [V7.2 Ridge Rule Protocol]
    Checks if the Archer can physically see the target.
    If occluded by terrain, the shot is blocked.
    """
    if not perception.can_see(player, target):
        player.send_line(f"{Colors.YELLOW}Your shot is blocked by a ridge of terrain!{Colors.RESET}")
        return False
    return True

@register("tracker_scan")
def handle_tracker_scan(player, skill, args, target=None):
    """Setup/Builder: Scan the area. (V6.8 Tactical Map Integration)"""
    player.send_line(f"{Colors.CYAN}You sweep your gaze across the horizon...{Colors.RESET}")
    # Trigger Intelligence Scan (Perception Matrix)
    p_result = perception.get_perception(player, radius=7, context=perception.INTELLIGENCE)
    
    # Reveal all entities found (Injecting into player's tracked state)
    count = 0
    if not hasattr(player, 'ext_state'): player.ext_state = {}
    player.ext_state.setdefault('tracked_entities', {})
    
    for (x, y), entities in p_result.entities.items():
        for ent in entities:
            player.ext_state['tracked_entities'][str(id(ent))] = player.game.tick_count
            count += 1
            if hasattr(ent, 'status_effects'):
                effects.apply_effect(ent, "revealed", 10)

    player.send_line(f"{Colors.GREEN}Scan complete. {count} signals pulses identified.{Colors.RESET}")
    _consume_resources(player, skill)
    return None, True

@register("target_lock")
def handle_target_lock(player, skill, args, target=None):
    """Setup: Mark a target for follow-up snipes."""
    target = common._get_target(player, args, target, "Lock on to whom?")
    if not target: return None, True
    
    # 1. Ridge Check (V7.2)
    if not _ridge_check(player, target, "Target Lock"):
        return None, True

    player.send_line(f"{Colors.BOLD}{Colors.CYAN}You focus your intent on {target.name}. (TARGET LOCKED){Colors.RESET}")
    effects.apply_effect(target, "marked", 12)
    
    # Generate Focus (URM)
    resources.modify_resource(player, "focus", 10, source="Target Lock")
    
    _consume_resources(player, skill)
    return target, True

@register("heartseeker_snipe")
def handle_heartseeker_snipe(player, skill, args, target=None):
    """Payoff/Finisher: massive damage vs Marked.
    [V7.2] Logic-Data Wall: Multiplier in JSON.
    """
    target = common._get_target(player, args, target, "Seek whose heart?")
    if not target: return None, True
    
    # 1. Ridge Check (V7.2)
    if not _ridge_check(player, target, "Heartseeker Snipe"):
        return None, True

    if effects.has_effect(target, "marked"):
        player.send_line(f"{Colors.BOLD}{Colors.RED}HEARTSEEKER! Your bolt finds its mark with uncanny precision!{Colors.RESET}")
    else:
        player.send_line(f"You loose a powerful bolt, but without a lock, it fails to find its path.")
        
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)

    _consume_resources(player, skill)
    return target, True

@register("volley_rain")
def handle_volley_rain(player, skill, args, target=None):
    """Payoff/AOE: Arcs OVER obstructions (Overrides Ridge Rule)."""
    player.send_line(f"{Colors.BOLD}{Colors.WHITE}VOLLEY RAIN! You launch a cluster of arrows high into the sky!{Colors.RESET}")
    
    # V7.1 Grammar: Arcs over ridgelines.
    # We do NOT run _ridge_check here because it's a high-arc volley.
    
    # Apply to all in room (Simplified AOE)
    targets = player.room.monsters + [p for p in player.room.players if p != player]
    for t in targets:
        combat.handle_attack(player, t, player.room, player.game, blessing=skill)
            
    _consume_resources(player, skill)
    return None, True

@register("catch_arrows")
def handle_catch_arrows(player, skill, args, target=None):
    """Defense: Reactionary dodge."""
    player.send_line(f"{Colors.GREEN}You prime your reflexes to catch incoming projectiles.{Colors.RESET}")
    effects.apply_effect(player, "catch_arrows_echo", 3) # Handled in combat engine core
    _consume_resources(player, skill)
    return None, True

@register("camouflage")
def handle_camouflage(player, skill, args, target=None):
    """Defense: Self-concealment."""
    player.send_line(f"{Colors.BOLD}{Colors.CYAN}You blend into the shadows of the environment.{Colors.RESET}")
    effects.apply_effect(player, "concealed", 8)
    _consume_resources(player, skill)
    return None, True

@register("archers_sprint")
def handle_archers_sprint(player, skill, args, target=None):
    """Mobility: Movement burst."""
    player.send_line(f"{Colors.WHITE}Your pulse quickens as you burst forward in a tactical sprint.{Colors.RESET}")
    
    # URM Clear CC
    if effects.has_effect(player, "slowed"): effects.remove_effect(player, "slowed")
    if effects.has_effect(player, "pinned"): effects.remove_effect(player, "pinned")
    
    effects.apply_effect(player, "haste", 2)
    _consume_resources(player, skill)
    return None, True

@register("pinnacle_of_arrows")
def handle_pinnacle_of_arrows(player, skill, args, target=None):
    """Utility/Ultimate: Enter Archer Flow."""
    player.send_line(f"{Colors.BOLD}{Colors.MAGENTA}PINNACLE OF ARROWS! You enter a state of perfect lethality.{Colors.RESET}")
    effects.apply_effect(player, "archer_flow", 3)
    # Grammar Check: Future skills check archer_flow to bypass costs.
    _consume_resources(player, skill)
    return None, True
