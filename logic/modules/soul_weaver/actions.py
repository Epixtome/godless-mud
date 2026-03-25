from logic.actions.registry import register
from utilities.colors import Colors
from logic.core import combat, resources, perception, messaging
import random

@register("weave_life")
def weave_life(player, target, blessing):
    """Setup: Channel life force. Restores 10 HP and applies [Regeneration]."""
    power = blessing.base_power
    heal = combat.calculate_heal(player, power, tags=["magic", "restoration"])
    
    target.receive_heal(player, heal, "life weaving")
    target.apply_status("regeneration", ticks=5, applier=player)
    
    player.send_line(f"You {Colors.BOLD}{Colors.WHITE}weave threads of life{Colors.RESET} into {target.name}.")
    target.room.broadcast(f"{player.name} {Colors.BOLD}{Colors.WHITE}weaves threads of life{Colors.RESET} into {target.name}!", exclude=[player])
    
    # Generate Spirits
    resources.modify_resource(player, "spirits", 1)
    return True

@register("sever_thread")
def sever_thread(player, target, blessing):
    """Setup: Rip at the target's spirit. Applies [Vulnerable]."""
    power = blessing.base_power
    damage = combat.calculate_damage(player, power, tags=["magic", "dark", "lethality"])
    
    target.receive_damage(player, damage, "spirit severing")
    target.apply_status("vulnerable", ticks=8, applier=player)
    
    player.send_line(f"You {Colors.BOLD}{Colors.RED}sever a thread of fate{Colors.RESET} from {target.name}, marking them for the void.")
    target.room.broadcast(f"{player.name} {Colors.BOLD}{Colors.RED}severs a thread of fate{Colors.RESET} from {target.name}!", exclude=[player])
    
    # Generate Spirits
    resources.modify_resource(player, "spirits", 2)
    return True

@register("soul_mending")
def soul_mending(player, target, blessing):
    """Payoff: Consume all [Regeneration] on allies to heal all in the room for 2x power."""
    power = blessing.base_power
    allies = [p for p in player.room.players] + [m for m in player.room.mobs if not m.is_hostile(player)]
    
    player.send_line(f"You pulse with {Colors.BOLD}{Colors.WHITE}Soul Mending{Colors.RESET}, pulling regeneration from all allies to heal in a flash!")
    
    for a in allies:
        # Count regen tags
        regen_count = 0
        if a.has_status("regeneration"): regen_count += 1
        
        mult = 1.0 + (regen_count * 1.0) # 2x per tag
        heal = combat.calculate_heal(player, power * mult, tags=["magic", "restoration", "aoe"])
        a.receive_heal(player, heal, "soul mending")
        if a.has_status("regeneration"): a.remove_status("regeneration")
        
    return True

@register("reaping_blast")
def reaping_blast(player, target, blessing):
    """Payoff: Explode all [Vulnerable] targets for massive Necrotic damage."""
    power = blessing.base_power
    if not target.has_status("vulnerable"):
        player.send_line(f"{target.name} must be vulnerable to reaping blast.")
        return False
        
    damage = combat.calculate_damage(player, power * 3.0, tags=["magic", "dark", "lethality"])
    target.receive_damage(player, damage, "reaping explosion")
    
    player.send_line(f"You {Colors.BOLD}{Colors.RED}detonate{Colors.RESET} your necrotic power inside {target.name}'s spirit!")
    target.room.broadcast(f"{player.name}'s power {Colors.BOLD}{Colors.RED}explodes{Colors.RESET} inside {target.name}!", exclude=[player])
    
    return True

@register("spiritual_barrier")
def spiritual_barrier(player, target, blessing):
    """Defense: Place a protective weave. Reduces damage by 30%."""
    player.apply_status("spiritual_barrier", ticks=30)
    player.send_line(f"A {Colors.WHITE}shield of shimmering threads{Colors.RESET} surrounds you.")
    return True

@register("soul_bind")
def soul_bind(player, target, blessing):
    """Defense: Bind your health with the target foe."""
    player.apply_status("soul_bind", ticks=60)
    target.apply_status("soul_bind", ticks=60)
    player.send_line(f"Your {Colors.MAGENTA}soul is tied{Colors.RESET} to {target.name}'s. Malice is now shared.")
    return True

@register("spirit_walk")
def spirit_walk(player, target, blessing):
    """Mobility: Step between realms. Grants [Concealed]."""
    player.apply_status("concealed", ticks=30)
    player.send_line(f"You {Colors.CYAN}flicker out of reality{Colors.RESET}, becoming a shadow ghost.")
    return True

@register("thread_of_fate")
def thread_of_fate(player, target, blessing):
    """Utility: Ultimate: For 15s, whenever an ally takes damage, its target enemy takes 50% of it."""
    player.apply_status("thread_of_fate", ticks=150)
    player.send_line(f"You pull the {Colors.BOLD}{Colors.MAGENTA}Thread of Fate{Colors.RESET}, entangling the malice of your enemies.")
    player.room.broadcast(f"The room glows with a {Colors.BOLD}{Colors.MAGENTA}shimmering net of spirits{Colors.RESET}!", exclude=[player])
    return True
