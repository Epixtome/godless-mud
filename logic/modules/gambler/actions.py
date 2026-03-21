"""
logic/modules/gambler/actions.py
Gambler Skill Handlers: Master of Probability and High Stakes.
V7.2 Standard Refactor (Baking Branch).
"""
import logging
import random
from logic.actions.registry import register
from logic.core import effects, resources, combat, perception
from logic.engines import action_manager, magic_engine
from utilities.colors import Colors
from logic import common

logger = logging.getLogger("GodlessMUD")

def _consume_resources(player, skill):
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)
    magic_engine.consume_pacing(player, skill)

@register("loaded_dice")
def handle_loaded_dice(player, skill, args, target=None):
    """[V7.2] Setup/Builder: Dice toss with Ridge Rule logic."""
    target = common._get_target(player, args, target, "Toss dice at whom?")
    if not target: return None, True
    
    # 1. Physics Gate (Ridge Rule)
    if not perception.can_see(player, target):
        player.send_line("The dice bounce off an unseen ridge.")
        return None, True

    player.send_line(f"{Colors.YELLOW}You roll the dice... the outcome was already written!{Colors.RESET}")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    
    # [V7.2] Luck via URM
    resources.modify_resource(player, "luck", 1, source="Loaded Dice")
    
    _consume_resources(player, skill)
    return target, True

@register("bad_beat")
def handle_bad_beat(player, skill, args, target=None):
    """[V7.2] Setup: Card flip with Ridge Rule."""
    target = common._get_target(player, args, target, "Flip cards for whom?")
    if not target: return None, True
    
    if not perception.can_see(player, target):
        player.send_line("The cards flutter into a ridge, hidden from the target.")
        return None, True

    player.send_line(f"{Colors.BLUE}A bad hand manifest as literal tragedy for {target.name}.{Colors.RESET}")
    effects.apply_effect(target, "off_balance", 4)
    effects.apply_effect(target, "confused", 4)
    _consume_resources(player, skill)
    return target, True

@register("ante_up")
def handle_ante_up(player, skill, args, target=None):
    """[V7.2] Setup: Marker with Ridge Rule sync."""
    target = common._get_target(player, args, target, "Raise the stakes for whom?")
    if not target: return None, True
    
    if not perception.can_see(player, target):
        player.send_line("The ante fails to reach the target.")
        return None, True

    player.send_line(f"{Colors.CYAN}You call {target.name}'s bluff. The stakes are now lethal.{Colors.RESET}")
    effects.apply_effect(target, "marked", 12)
    _consume_resources(player, skill)
    return target, True

@register("jackpot")
def handle_jackpot(player, skill, args, target=None):
    """[V7.2] Payoff/Burst: Randomized strike with Ridge Rule & Logic-Data Wall."""
    target = common._get_target(player, args, target, "The final spin for whom?")
    if not target: return None, True
    
    if not perception.can_see(player, target):
        player.send_line("The jackpot is cancelled; target is hidden.")
        return None, True

    # [V7.2] Pips from URM
    luck_pips = resources.get_resource(player, "luck")
    if luck_pips < 3:
         player.send_line(f"You need at least 3 Luck Pips to trigger a Jackpot spin.")
         return None, True
         
    player.send_line(f"{Colors.BOLD}{Colors.WHITE}The slot reels spin...{Colors.RESET}")
    
    # [V7.2] Randomized multipliers and critical outcomes handled in evaluation engine/JSON rules.
    # The action logic provides visual feedback and triggers the URM consumption.
    chance = random.random()
    if chance < 0.05:
         player.send_line(f"{Colors.BOLD}{Colors.YELLOW}JACKPOT! 777! Triple payout!{Colors.RESET}")
    else:
         player.send_line(f"{Colors.WHITE}Double payout!{Colors.RESET}")
         
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    
    # Consume Luck Pips via URM
    resources.modify_resource(player, "luck", -luck_pips, source="Jackpot Spin")
    
    _consume_resources(player, skill)
    return target, True

@register("all_in")
def handle_all_in(player, skill, args, target=None):
    """[V7.2] Finisher: Mass payoff via Luck with Ridge Rule."""
    target = common._get_target(player, args, target, "All in on whom?")
    if not target: return None, True
    
    if not perception.can_see(player, target):
        player.send_line("All in on a ghost? Target is hidden.")
        return None, True

    player.send_line(f"{Colors.BOLD}{Colors.WHITE}ALL IN! You commit every card in your hand to this single strike!{Colors.RESET}")
    
    # Reset all class cooldowns (50% chance as per original design/legacy spirit)
    if random.random() < 0.5:
        player.send_line(f"{Colors.BOLD}{Colors.GREEN}THE COARSE CORRECTOR! All cooldowns have been reset!{Colors.RESET}")
        magic_engine.clear_all_cooldowns(player)
    
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    
    # Resets luck to zero via URM
    luck = resources.get_resource(player, "luck")
    resources.modify_resource(player, "luck", -luck, source="All In Execution")
             
    _consume_resources(player, skill)
    return target, True

@register("lucky_break")
def handle_lucky_break(player, skill, args, target=None):
    """Defense: Self-reaction evasion."""
    player.send_line(f"{Colors.CYAN}Fates favor the bold! You feel a divine push out of harm's eye.{Colors.RESET}")
    effects.apply_effect(player, "lucky_evasion", 4)
    _consume_resources(player, skill)
    return None, True

@register("shuffle")
def handle_shuffle(player, skill, args, target=None):
    """[V7.2] Mobility: Linear dash with confuse AoE logic."""
    player.send_line(f"{Colors.BOLD}{Colors.WHITE}The shuffle begins! You vanish and reform elsewhere.{Colors.RESET}")
    effects.apply_effect(player, "haste", 2)
    # Target shift - confuse all mobs in room
    for m in player.room.monsters:
        if perception.can_see(player, m):
            effects.apply_effect(m, "confused", 2)
            
    _consume_resources(player, skill)
    return None, True

@register("high_stakes")
def handle_high_stakes(player, skill, args, target=None):
    """Utility/Buff: High-risk crit mode."""
    player.send_line(f"{Colors.BOLD}{Colors.RED}HIGH STAKES! Next hit is life or death.{Colors.RESET}")
    if 'gambler' in player.ext_state:
        player.ext_state['gambler']['high_stakes_active'] = True
    _consume_resources(player, skill)
    return None, True
