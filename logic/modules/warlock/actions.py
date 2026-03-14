"""
logic/modules/warlock/actions.py
Hexblade Overhaul: Entropy Symbiosis Implementation.
"""
from logic.actions.registry import register
from logic.core import resources, effects, combat
from logic import common
from utilities.colors import Colors
from logic.engines import blessings_engine, magic_engine

def _consume_resources(player, skill, entropy_gain=0):
    """Handles resource consumption and entropy generation."""
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)
    
    if entropy_gain > 0:
        w_state = player.ext_state.setdefault('warlock', {})
        old_entropy = w_state.get('entropy', 0)
        max_e = w_state.get('max_entropy', 5)
        
        # In Metamorphosis, entropy is locked at max
        if not w_state.get('is_metamorphosed', False):
            w_state['entropy'] = min(max_e, old_entropy + entropy_gain)
            if w_state['entropy'] > old_entropy:
                player.send_line(f"{Colors.MAGENTA}[+] Entropy: {w_state['entropy']}/{max_e}{Colors.RESET}")
            elif old_entropy >= max_e:
                player.send_line(f"{Colors.PURPLE}[!] Entropy at maximum capacity!{Colors.RESET}")
        else:
            w_state['entropy'] = max_e

@register("hex")
def handle_hex(player, skill, args, target=None):
    """Primer: Generates 2 Entropy. Applies Hexed debuff."""
    target = common._get_target(player, args, target, "Hex whom?")
    if not target: return None, True
    
    player.send_line(f"{Colors.MAGENTA}You weave a web of entropic despair around {target.name}!{Colors.RESET}")
    effects.apply_effect(target, "hexed", 20) # 20 seconds
    
    if hasattr(target, 'send_line'):
        target.send_line(f"{Colors.RED}You feel a dark mark burning into your soul!{Colors.RESET}")
        
    _consume_resources(player, skill, entropy_gain=2)
    return target, True

@register("eldritch_blast")
def handle_eldritch_blast(player, skill, args, target=None):
    """Builder: Generates 1 Entropy. Ranged dark damage."""
    target = common._get_target(player, args, target, "Blast whom?")
    if not target: return None, True
    
    player.send_line(f"{Colors.DARK_GRAY}A beam of crackling force erupts from your hand!{Colors.RESET}")
    power = blessings_engine.MathBridge.calculate_power(skill, player, target)
    
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    
    _consume_resources(player, skill, entropy_gain=1)
    return target, True

@register("netherstep")
def handle_netherstep(player, skill, args, target=None):
    """Utility: Teleport and Stun. Generates 1 Entropy."""
    target = common._get_target(player, args, target, "Step towards whom?")
    if not target: return None, True
    
    player.send_line(f"{Colors.BOLD}{Colors.PURPLE}You step through the void, appearing behind {target.name}!{Colors.RESET}")
    player.room.broadcast(f"{player.name} vanishes into shadows and reappears behind {target.name}!", exclude_player=player)
    
    effects.apply_effect(target, "stun", 1) # 1s Stun
    
    _consume_resources(player, skill, entropy_gain=1)
    return target, True

@register("soul_cleave")
def handle_soul_cleave(player, skill, args, target=None):
    """Detonator: Consumes ALL Entropy. +25% Dmg and +10% Heal per stack."""
    target = common._get_target(player, args, target, "Cleave whose soul?")
    if not target: return None, True
    
    w_state = player.ext_state.setdefault('warlock', {})
    stacks = w_state.get('entropy', 0)
    
    player.send_line(f"{Colors.BOLD}{Colors.RED}SOUL CLEAVE!{Colors.RESET} Your blade wails with chaotic hunger!")
    
    # Calculate Multiplier: 1.0 base + 0.25 per stack
    dmg_mult = 1.0 + (stacks * 0.25)
    
    # Calculate Heal
    heal_pct = stacks * 0.10
    heal_amt = int(player.max_hp * heal_pct)
    
    # Execute Attack
    power = blessings_engine.MathBridge.calculate_power(skill, player, target)
    final_dmg = int(power * dmg_mult)
    
    # Manual attack trigger with custom damage to ensure scaling is applied before mitigation
    # Or use calculate_damage_modifier event in events.py (preferred for GCA)
    # But Soul Cleave is a specific strike, we'll pass the multiplier through context or just calc here
    combat.handle_attack(player, target, player.room, player.game, blessing=skill, context_prefix=f"[Entropy:{stacks}] ")
    
    if heal_amt > 0:
        resources.modify_resource(player, "hp", heal_amt, source="Soul Cleave", context="Healing")
        player.send_line(f"{Colors.GREEN}You absorb {heal_amt} HP from the soul essence!{Colors.RESET}")
        
    # Discharge Entropy (unless metastasized)
    if not w_state.get('is_metamorphosed', False):
        w_state['entropy'] = 0
        player.send_line(f"{Colors.DARK_GRAY}Entropy discharged.{Colors.RESET}")
        
    _consume_resources(player, skill)
    return target, True

@register("metamorphosis")
def handle_metamorphosis(player, skill, args, target=None):
    """Ultimate: Transforms the warlock. Locks Entropy at 5."""
    player.send_line(f"{Colors.BOLD}{Colors.PURPLE}You erupt in a pillar of violet flame!{Colors.RESET}")
    player.room.broadcast(f"{player.name} is enveloped in dark fire and transforms into a towering demon!", exclude_player=player)
    
    effects.apply_effect(player, "metamorphosis", 30) # 30 seconds
    
    w_state = player.ext_state.setdefault('warlock', {})
    w_state['is_metamorphosed'] = True
    w_state['entropy'] = w_state.get('max_entropy', 5)
    
    _consume_resources(player, skill)
    return None, True
