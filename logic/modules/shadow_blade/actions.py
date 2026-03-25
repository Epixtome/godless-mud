from logic.actions.registry import register
from utilities.colors import Colors
from logic.core import combat, resources, perception, messaging
import random

@register("void_strike")
def void_strike(player, target, blessing):
    """Setup: Strike with a shadowed blade. Deals damage and applies [Marked]."""
    power = blessing.base_power
    damage = combat.calculate_damage(player, power, tags=["martial", "dark", "lethality"])
    
    target.receive_damage(player, damage, "shadowy blade")
    target.apply_status("marked", ticks=15, applier=player)
    
    player.send_line(f"Your blade leaves a {Colors.MAGENTA}dark trail{Colors.RESET} across {target.name}, marking them for the void.")
    target.room.broadcast(f"{player.name}'s blade leaves a {Colors.MAGENTA}dark trail{Colors.RESET} across {target.name}!", exclude=[player])
    
    # Generate Stamina
    resources.modify_resource(player, "stamina", 10)
    return True

@register("shadow_meld")
def shadow_meld(player, target, blessing):
    """Setup: Fade into the void. Grants [Concealed] for 200 ticks."""
    player.apply_status("concealed", ticks=200)
    player.send_line(f"You {Colors.DGREY}fade into the void{Colors.RESET}, vanishing from sight.")
    player.room.broadcast(f"{player.name} {Colors.DGREY}vanishes into the shadows{Colors.RESET}!", exclude=[player])
    return True

@register("assassinate")
def assassinate(player, target, blessing):
    """Payoff: Deliver a lethal blow to a [Marked] target. Deals 4x damage from [Concealed]."""
    if not player.has_status("concealed"):
        player.send_line("You must be concealed to assassinate.")
        return False
        
    power = blessing.base_power
    multiplier = 4.0 if target.has_status("marked") else 1.5
    
    damage = combat.calculate_damage(player, power * multiplier, tags=["martial", "lethality"])
    target.receive_damage(player, damage, "lethal assassination")
    
    player.remove_status("concealed")
    player.send_line(f"You step from the void and {Colors.RED}strike through{Colors.RESET} {target.name}'s heart!")
    target.room.broadcast(f"{player.name} steps from the void and {Colors.RED}plunges a blade{Colors.RESET} into {target.name}!", exclude=[player])
    
    return True

@register("twilight_dance")
def twilight_dance(player, target, blessing):
    """Payoff: Whirling blades of shadow. Deals Area damage to all enemies in the room."""
    power = blessing.base_power
    targets = [m for m in player.room.mobs if m.is_hostile(player)]
    
    player.send_line(f"You perform a {Colors.MAGENTA}Twilight Dance{Colors.RESET}, your blades becoming a blur of darkness.")
    
    for t in targets:
        mult = 2.0 if t.has_status("marked") else 1.0
        damage = combat.calculate_damage(player, power * mult, tags=["martial", "dark", "aoe"])
        t.receive_damage(player, damage, "twilight blades")
        if t.has_status("marked"):
            t.remove_status("marked")
            
    return True

@register("void_parry")
def void_parry(player, target, blessing):
    """Defense: Parry the next attack, absorbing 50% damage."""
    player.apply_status("void_parry", ticks=5)
    player.send_line(f"You raise your blade, weaving a {Colors.CYAN}net of shadows{Colors.RESET} around you.")
    return True

@register("ghost_form")
def ghost_form(player, target, blessing):
    """Defense: Turn ethereal for 5s, granting 50% Evasion."""
    player.apply_status("ghost_form", ticks=50) # 5 seconds approx
    player.send_line(f"You become {Colors.WHITE}ethereal{Colors.RESET}, your body turning to grey mist.")
    return True

@register("night_step")
def night_step(player, target, blessing):
    """Mobility: Blink to an adjacent room instantly."""
    # Logic for room movement
    exits = player.room.exits
    if not exits:
        player.send_line("There are no exits to step through.")
        return False
        
    # Pick a random exit if no direction provided, or just let them pick?
    # For now, let's assume it picks a random adjacent room.
    target_room = random.choice(list(exits.values()))
    player.room.broadcast(f"{player.name} {Colors.DGREY}dissolves into shadows{Colors.RESET} and is gone.", exclude=[player])
    player.move_to(target_room)
    player.send_line(f"You emerge from the shadows in {target_room.name}.")
    target_room.broadcast(f"{player.name} {Colors.DGREY}emerges from the shadows{Colors.RESET}.", exclude=[player])
    return True

@register("dark_vision")
def dark_vision(player, target, blessing):
    """Utility: Reveal all hidden entities in the room."""
    player.apply_status("dark_vision", ticks=200)
    player.send_line(f"Your eyes glow with {Colors.BOLD}{Colors.MAGENTA}Abyssal Light{Colors.RESET}, revealing the unseen.")
    
    hidden = [m for m in player.room.mobs if m.has_status("concealed")]
    for h in hidden:
        h.remove_status("concealed")
        player.send_line(f"You have revealed {h.name}!")
        
    return True
