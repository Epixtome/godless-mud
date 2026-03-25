from logic.actions.registry import register
from utilities.colors import Colors
from logic.core import combat, resources, perception, messaging
import random

@register("twilight_strike")
def twilight_strike(player, target, blessing):
    """Setup: Strike with dark grace. Deals damage and applies [Off-Balance]."""
    power = blessing.base_power
    damage = combat.calculate_damage(player, power, tags=["martial", "speed", "dark"])
    
    target.receive_damage(player, damage, "twilight strike")
    target.apply_status("off_balance", ticks=5, applier=player)
    
    player.send_line(f"You {Colors.BOLD}{Colors.MAGENTA}dance through{Colors.RESET} {target.name}, striking with dark grace.")
    target.room.broadcast(f"{player.name} {Colors.BOLD}{Colors.MAGENTA}dances through{Colors.RESET} {target.name}!", exclude=[player])
    
    # Generate Rhythm
    resources.modify_resource(player, "rhythm", 15)
    return True

@register("shadow_step")
def shadow_step(player, target, blessing):
    """Setup: Dash into the target's shadow. Gains [Concealed] and applies [Marked]."""
    player.apply_status("concealed", ticks=15, applier=player)
    target.apply_status("marked", ticks=10, applier=player)
    
    player.send_line(f"You {Colors.DGREY}vanish into the shadow{Colors.RESET} of {target.name}, marking them for the void.")
    target.room.broadcast(f"{player.name} {Colors.DGREY}slides into the shadow{Colors.RESET} of {target.name}!", exclude=[player])
    return True

@register("danse_macabre")
def danse_macabre(player, target, blessing):
    """Payoff: Perform a lethal dance. Deals 1.2x damage per point of Speed resonance."""
    power = blessing.base_power
    
    # Using Speed resonance as multiplier (V7.2)
    speed_resonance = player.current_tags.get("speed", 0)
    mult = 1.0 + (speed_resonance * 0.1) # 1.1x per speed tag
    
    damage = combat.calculate_damage(player, power * mult, tags=["martial", "lethality", "speed"])
    target.receive_damage(player, damage, "danse macabre")
    
    # Consume Rhythm
    resources.modify_resource(player, "rhythm", -100) # consume all
    
    player.send_line(f"You perform a {Colors.BOLD}{Colors.RED}Danse Macabre{Colors.RESET}, your blades becoming a lethal blur of speed!")
    target.room.broadcast(f"{player.name} performs a {Colors.BOLD}{Colors.RED}Danse Macabre{Colors.RESET} on {target.name}!", exclude=[player])
    
    return True

@register("sever_soul")
def sever_soul(player, target, blessing):
    """Payoff: A final, lethal flourish. Deals 3x damage if target is [Off-Balance]."""
    if not target.has_status("off_balance"):
        player.send_line(f"{target.name} must be off-balance to sever soul.")
        return False
        
    power = blessing.base_power
    damage = combat.calculate_damage(player, power * 3.0, tags=["martial", "lethality", "dark"])
    target.receive_damage(player, damage, "soul severing flourish")
    
    player.send_line(f"You {Colors.BOLD}{Colors.RED}sever the soul{Colors.RESET} of {target.name} in a final, lethal flourish!")
    target.room.broadcast(f"{player.name} {Colors.BOLD}{Colors.RED}severs the soul{Colors.RESET} of {target.name}!", exclude=[player])
    
    return True

@register("evasive_waltz")
def evasive_waltz(player, target, blessing):
    """Defense: Increase Evasion by 50% for 6s."""
    player.apply_status("evasive_waltz", ticks=60)
    player.send_line(f"You begin an {Colors.CYAN}Evasive Waltz{Colors.RESET}, flowing between incoming strikes.")
    return True

@register("shadow_echo")
def shadow_echo(player, target, blessing):
    """Defense: Leave behind a shadow clone for 5s."""
    player.apply_status("shadow_echo", ticks=50)
    player.send_line(f"A {Colors.DGREY}shimmering shadow echo{Colors.RESET} takes your place in the void.")
    return True

@register("flicker")
def flicker(player, target, blessing):
    """Mobility: Instantly blink to an adjacent room."""
    exits = player.room.exits
    if not exits:
        player.send_line("There are no shadows to flicker to.")
        return False
        
    target_room = random.choice(list(exits.values()))
    player.room.broadcast(f"{player.name} {Colors.BOLD}{Colors.MAGENTA}flickers through space{Colors.RESET} and is gone.", exclude=[player])
    player.move_to(target_room)
    player.send_line(f"You emerge from a flicker shimmer in {target_room.name}.")
    target_room.broadcast(f"{player.name} {Colors.BOLD}{Colors.MAGENTA}emerges from a flicker shimmer{Colors.RESET}.", exclude=[player])
    return True

@register("eclipse_curse")
def eclipse_curse(player, target, blessing):
    """Utility: Ultimate: For 20s, all your attacks have a 50% chance to apply [Blinded]."""
    player.apply_status("eclipse_curse", ticks=200)
    player.send_line(f"You cast an {Colors.BOLD}{Colors.DGREY}Eclipse Curse{Colors.RESET}, turning the room to eternal night.")
    player.room.broadcast(f"The room turns to {Colors.BOLD}{Colors.DGREY}eternal night{Colors.RESET} as {player.name} casts an Eclipse Curse!", exclude=[player])
    return True
