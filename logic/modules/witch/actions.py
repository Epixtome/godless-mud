from logic.actions.registry import register
from utilities.colors import Colors
from logic.core import combat, resources, perception, messaging
import random

@register("hex_flare")
def hex_flare(player, target, blessing):
    """Setup: Pulse of dark energy. Applies [Hexed] to all in the room."""
    power = blessing.base_power
    targets = [m for m in player.room.mobs if m.is_hostile(player)]
    
    player.send_line(f"You pulse with {Colors.GREEN}Hexing Light{Colors.RESET}, marking the fates of your enemies.")
    
    for t in targets:
        damage = combat.calculate_damage(player, power, tags=["occult", "dark", "aoe"])
        t.receive_damage(player, damage, "hexing pulse")
        t.apply_status("hexed", ticks=12, applier=player)
        
    # Generate Entropy
    resources.modify_resource(player, "entropy", 15)
    return True

@register("curse_of_binding")
def curse_of_binding(player, target, blessing):
    """Setup: Bind the foe's shadows. Applies [Cursed]."""
    power = blessing.base_power
    target.apply_status("cursed", ticks=15, applier=player)
    target.apply_status("slowed", ticks=10, applier=player)
    
    player.send_line(f"You {Colors.BOLD}{Colors.MAGENTA}bind the shadows{Colors.RESET} of {target.name}, pinning them in place.")
    target.room.broadcast(f"{player.name} {Colors.BOLD}{Colors.MAGENTA}binds the shadows{Colors.RESET} of {target.name}!", exclude=[player])
    return True

@register("vile_curse")
def vile_curse(player, target, blessing):
    """Payoff: Consume [Hexed] and [Cursed] to deal massive Entropy damage."""
    if not target.has_status("hexed") and not target.has_status("cursed"):
        player.send_line(f"{target.name} must be hexed or cursed to vile curse.")
        return False
        
    power = blessing.base_power
    count = 0
    if target.has_status("hexed"): count += 1
    if target.has_status("cursed"): count += 1
    
    damage = combat.calculate_damage(player, power * (3.0 * count), tags=["occult", "dark", "lethality"])
    target.receive_damage(player, damage, "vile curse detonation")
    
    player.send_line(f"You detonate your {Colors.RED}maleficent energy{Colors.RESET} inside {target.name}!")
    target.room.broadcast(f"{player.name}'s curses {Colors.RED}detonate{Colors.RESET} inside {target.name}!", exclude=[player])
    
    # Remove states
    target.remove_status("hexed")
    target.remove_status("cursed")
    return True

@register("soul_siphon")
def soul_siphon(player, target, blessing):
    """Payoff: Drain 20% of target health if they are [Hexed]."""
    if not target.has_status("hexed"):
        player.send_line(f"{target.name} must be hexed to soul siphon.")
        return False
        
    power = blessing.base_power
    drain_amount = int(target.max_hp * 0.2)
    target.receive_damage(player, drain_amount, "soul siphon", true_damage=True)
    player.receive_heal(player, drain_amount, "stolen soul")
    
    player.send_line(f"You {Colors.GREEN}siphon the soul{Colors.RESET} of {target.name}, drinking their life force.")
    target.room.broadcast(f"{player.name} {Colors.GREEN}siphons the soul{Colors.RESET} of {target.name}!", exclude=[player])
    
    return True

@register("fate_mirror")
def fate_mirror(player, target, blessing):
    """Defense: Refract 50% of the next attack damage back."""
    player.apply_status("fate_mirror", ticks=15)
    player.send_line(f"You hold up a {Colors.WHITE}fractured glass of time{Colors.RESET}, mirroring malice.")
    return True

@register("mist_form")
def mist_form(player, target, blessing):
    """Defense: Turn into dark mist, becoming untargetable for 3s."""
    player.apply_status("mist_form", ticks=30)
    player.send_line(f"You dissolve into a {Colors.DGREY}dark mist{Colors.RESET}, flowing between blows.")
    return True

@register("night_shade")
def night_shade(player, target, blessing):
    """Mobility: Dash forward through enemies, applying [Blinded]."""
    player.send_line(f"You slide through {Colors.DGREY}night shade{Colors.RESET}, blinding all you pass.")
    
    targets = [m for m in player.room.mobs if m.is_hostile(player)]
    for t in targets:
        t.apply_status("blinded", ticks=5, applier=player)
        
    return True

@register("dark_ritual")
def dark_ritual(player, target, blessing):
    """Utility: For 20s, all [Cursed] targets take 2x damage from all sources."""
    player.apply_status("dark_ritual", ticks=200)
    player.send_line(f"You perform a {Colors.BOLD}{Colors.RED}Dark Ritual{Colors.RESET}, marking the end for your enemies.")
    player.room.broadcast(f"The air turns cold as {player.name} performs a {Colors.BOLD}{Colors.RED}Dark Ritual{Colors.RESET}!", exclude=[player])
    return True
