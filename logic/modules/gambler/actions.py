"""
logic/modules/gambler/actions.py
Gambler Skill Handlers: Master of Probability and High Stakes.
Pillar: Tempo Axis, Randomization, and High Risk/High Reward payoffs.
"""
import random
from logic.actions.registry import register
from logic.core import effects, resources, combat
from logic.engines import action_manager, magic_engine
from utilities.colors import Colors
from logic import common

def _consume_resources(player, skill):
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)
    magic_engine.consume_pacing(player, skill)

@register("loaded_dice")
def handle_loaded_dice(player, skill, args, target=None):
    """Setup/Builder: Roll for data and luck pips."""
    target = common._get_target(player, args, target, "Toss dice at whom?")
    if not target: return None, True
    
    player.send_line(f"{Colors.YELLOW}You roll the dice... the outcome was already written!{Colors.RESET}")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    resources.modify_resource(player, "luck", 1, source="Loaded Dice")
    _consume_resources(player, skill)
    return target, True

@register("bad_beat")
def handle_bad_beat(player, skill, args, target=None):
    """Setup: [Off-Balance] and [Confused]."""
    target = common._get_target(player, args, target, "Flip cards for whom?")
    if not target: return None, True
    
    player.send_line(f"{Colors.BLUE}A bad hand manifest as literal tragedy for {target.name}.{Colors.RESET}")
    effects.apply_effect(target, "off_balance", 4)
    effects.apply_effect(target, "confused", 4)
    _consume_resources(player, skill)
    return target, True

@register("ante_up")
def handle_ante_up(player, skill, args, target=None):
    """Setup: [Marked] for double payoffs."""
    target = common._get_target(player, args, target, "Raise the stakes for whom?")
    if not target: return None, True
    
    player.send_line(f"{Colors.CYAN}You call {target.name}'s bluff. The stakes are now lethal.{Colors.RESET}")
    effects.apply_effect(target, "marked", 12)
    _consume_resources(player, skill)
    return target, True

@register("jackpot")
def handle_jackpot(player, skill, args, target=None):
    """Payoff/Burst: big damage vs luck pips."""
    target = common._get_target(player, args, target, "The final spin for whom?")
    if not target: return None, True
    
    luck_pips = player.ext_state.get('gambler', {}).get('luck', 0)
    if luck_pips < 3:
         player.send_line(f"You need at least 3 Luck Pips to trigger a Jackpot spin.")
         return None, True
         
    player.send_line(f"{Colors.BOLD}{Colors.WHITE}The slot reels spin...{Colors.RESET}")
    
    chance = random.random()
    if chance < 0.05: # 5% Insta-payoff
         player.send_line(f"{Colors.BOLD}{Colors.YELLOW}JACKPOT! 777! Triple payout!{Colors.RESET}")
         player.jackpot_multiplier = 10.0
    else:
         player.send_line(f"{Colors.WHITE}Double payout!{Colors.RESET}")
         player.jackpot_multiplier = 2.0 + (luck_pips * 0.2)
         
    try:
         combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    finally:
         if hasattr(player, 'jackpot_multiplier'): del player.jackpot_multiplier
             
    player.ext_state['gambler']['luck'] = 0
    _consume_resources(player, skill)
    return target, True

@register("all_in")
def handle_all_in(player, skill, args, target=None):
    """Payoff/Finisher: massive physical strike + resets."""
    target = common._get_target(player, args, target, "All in on whom?")
    if not target: return None, True
    
    player.send_line(f"{Colors.BOLD}{Colors.WHITE}ALL IN! You commit every card in your hand to this single strike!{Colors.RESET}")
    
    if random.random() < 0.5:
        player.send_line(f"{Colors.BOLD}{Colors.GREEN}THE COARSE CORRECTOR! All cooldowns have been reset!{Colors.RESET}")
        # Logic to reset cooldowns here
    
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    player.ext_state['gambler']['luck'] = 0
    _consume_resources(player, skill)
    return target, True

@register("lucky_break")
def handle_lucky_break(player, skill, args, target=None):
    """Defense: Self-reaction evasion."""
    player.send_line(f"{Colors.CYAN}Fates favor the bold! You feel a divine push out of harm's eye.{Colors.RESET}")
    effects.apply_effect(player, "lucky_evasion", 4) # 30% chance to ignore hit logic
    _consume_resources(player, skill)
    return None, True

@register("shuffle")
def handle_shuffle(player, skill, args, target=None):
    """Mobility: blink and confuse."""
    player.send_line(f"{Colors.BOLD}{Colors.WHITE}The shuffle begins! You vanish and reform elsewhere.{Colors.RESET}")
    effects.apply_effect(player, "haste", 2)
    # Target shift logic?
    _consume_resources(player, skill)
    return None, True

@register("high_stakes")
def handle_high_stakes(player, skill, args, target=None):
    """Utility/Buff: Ultimate focus mode."""
    player.send_line(f"{Colors.BOLD}{Colors.RED}HIGH STAKES! Next hit is life or death.{Colors.RESET}")
    player.ext_state['gambler']['high_stakes_active'] = True
    # Logic in handle_attack to guarantee crit or kill user
    _consume_resources(player, skill)
    return None, True
