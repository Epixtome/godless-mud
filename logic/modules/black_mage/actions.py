from logic.actions.registry import register
from utilities.colors import Colors
from logic.core import combat, resources, perception, messaging
import random

@register("hellfire_cast")
def hellfire_cast(player, target, blessing):
    """Setup: Imbue with Dark Fire. Deals damage and applies [Burning]."""
    power = blessing.base_power
    damage = combat.calculate_damage(player, power, tags=["magic", "fire", "dark"])
    
    target.receive_damage(player, damage, "dark hellfire")
    target.apply_status("burning", ticks=10, applier=player)
    
    player.send_line(f"You weave {Colors.BOLD}{Colors.YELLOW}Hellfire{Colors.RESET} around {target.name}, scorching their soul.")
    target.room.broadcast(f"{player.name} weaves {Colors.BOLD}{Colors.YELLOW}Hellfire{Colors.RESET} around {target.name}!", exclude=[player])
    
    # Generate Concentration
    resources.modify_resource(player, "concentration", 10)
    return True

@register("abyssal_chill")
def abyssal_chill(player, target, blessing):
    """Setup: Draw from the cold void. Deals damage and applies [Chilled]."""
    power = blessing.base_power
    damage = combat.calculate_damage(player, power, tags=["magic", "ice", "dark"])
    
    target.receive_damage(player, damage, "abyssal chill")
    target.apply_status("chilled", ticks=10, applier=player)
    
    player.send_line(f"The {Colors.CYAN}Cold Void{Colors.RESET} grips {target.name}, slowing their pulse.")
    target.room.broadcast(f"The {Colors.CYAN}Cold Void{Colors.RESET} grips {target.name}!", exclude=[player])
    
    # Generate Concentration
    resources.modify_resource(player, "concentration", 10)
    return True

@register("cataclysmic_burst")
def cataclysmic_burst(player, target, blessing):
    """Payoff: Explode all elemental states in the room for massive AOE Necrotic damage."""
    power = blessing.base_power
    targets = [m for m in player.room.mobs if m.is_hostile(player)]
    
    player.send_line(f"You command a {Colors.BOLD}{Colors.MAGENTA}Cataclysmic Burst{Colors.RESET}, turning elements into pure entropy!")
    
    for t in targets:
        # Count elemental tags (burning, chilled, shock, etc.)
        elemental_tags = 0
        for tag in ["burning", "chilled", "wet", "shocked"]:
            if t.has_status(tag):
                elemental_tags += 1
                
        mult = 1.0 + (elemental_tags * 1.0) # 2x per tag
        damage = combat.calculate_damage(player, power * mult, tags=["magic", "dark", "aoe"])
        t.receive_damage(player, damage, "cataclysmic explosion")
        
    player.room.broadcast(f"{player.name} unleashes a {Colors.BOLD}{Colors.MAGENTA}Cataclysmic Burst{Colors.RESET} that shreds the room!", exclude=[player])
    return True

@register("soul_ignite")
def soul_ignite(player, target, blessing):
    """Payoff: Consume [Burning] to deal 3x direct necrotic damage."""
    if not target.has_status("burning"):
        player.send_line(f"{target.name} must be burning to soul ignite.")
        return False
        
    power = blessing.base_power
    damage = combat.calculate_damage(player, power * 3.0, tags=["magic", "dark", "lethality"])
    target.receive_damage(player, damage, "soul ignition")
    
    player.send_line(f"You ignite {target.name}'s soul, {Colors.YELLOW}sacrificing their body{Colors.RESET} to the dark flame!")
    target.room.broadcast(f"{player.name} ignites {target.name}'s soul in a flash of {Colors.YELLOW}dark flame{Colors.RESET}!", exclude=[player])
    
    return True

@register("obsidian_barrier")
def obsidian_barrier(player, target, blessing):
    """Defense: Surround yourself with dark energy. Absorbs 40% Magical damage."""
    player.apply_status("obsidian_barrier", ticks=20)
    player.send_line(f"You pull {Colors.DGREY}Obsidian Shards{Colors.RESET} from the air, forming an anti-magic shield.")
    return True

@register("mana_parry")
def mana_parry(player, target, blessing):
    """Defense: Redirect incoming spell damage into your own Concentration reservoir."""
    player.apply_status("mana_parry", ticks=10)
    player.send_line(f"You open a {Colors.BOLD}{Colors.MAGENTA}Siphon Void{Colors.RESET}, eager to consume mental energy.")
    return True

@register("rift_dash")
def rift_dash(player, target, blessing):
    """Mobility: Blink to an adjacent room instantly."""
    exits = player.room.exits
    if not exits:
        player.send_line("There are no rifts to step through.")
        return False
        
    target_room = random.choice(list(exits.values()))
    player.room.broadcast(f"{player.name} {Colors.BOLD}{Colors.MAGENTA}blinks across space{Colors.RESET} and is gone.", exclude=[player])
    player.move_to(target_room)
    player.send_line(f"You emerge from a rift in {target_room.name}.")
    target_room.broadcast(f"{player.name} {Colors.BOLD}{Colors.MAGENTA}emerges from a rift{Colors.RESET}.", exclude=[player])
    return True

@register("dark_ascendancy")
def dark_ascendancy(player, target, blessing):
    """Utility: Ultimate: For 15s, your Concentration cost is halved and all spells are instant cast."""
    player.apply_status("dark_ascendancy", ticks=150)
    player.send_line(f"You embrace {Colors.BOLD}{Colors.RED}Dark Ascendancy{Colors.RESET}. You are the weaver of destruction!")
    player.room.broadcast(f"{player.name} {Colors.BOLD}{Colors.RED}glows with catastrophic power{Colors.RESET}!", exclude=[player])
    return True
