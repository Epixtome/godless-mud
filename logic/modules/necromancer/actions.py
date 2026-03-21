"""
logic/modules/necromancer/actions.py
Necromancer Skill Handlers: Master of Decay and Servitude.
V7.2 Standard Refactor (Baking Branch).
"""
import logging
from logic.actions.registry import register
from logic.core import effects, resources, combat, perception
from logic.engines import action_manager, magic_engine
from utilities.colors import Colors
from logic import common
from models import Corpse
from logic.core import follower_service

logger = logging.getLogger("GodlessMUD")

def _consume_resources(player, skill):
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)
    magic_engine.consume_pacing(player, skill)

@register("bone_spike")
def handle_bone_spike(player, skill, args, target=None):
    """[V7.2] Setup/Builder: Piercing damage and Entropy generation with Ridge Rule."""
    target = common._get_target(player, args, target, "Pierce whose soul?")
    if not target: return None, True
    
    # 1. Physics Gate (Ridge Rule)
    if not perception.can_see(player, target):
        player.send_line("Terrain blocks the path of your bone spike.")
        return None, True

    player.send_line(f"{Colors.BLUE}You launch a jagged bone spike, tearing into {target.name}!{Colors.RESET}")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    
    # [V7.2] Entropy via URM
    resources.modify_resource(player, "entropy", 1, source="Bone Spike")
    effects.apply_effect(target, "bleeding", 3)
    
    _consume_resources(player, skill)
    return target, True

@register("soul_shackles")
def handle_soul_shackles(player, skill, args, target=None):
    """Setup: [Shackled] and [Marked] applier."""
    target = common._get_target(player, args, target, "Shackle whom?")
    if not target: return None, True
    
    # 1. Physics Gate
    if not perception.can_see(player, target):
        player.send_line("Spectral chains cannot find their target through the terrain.")
        return None, True

    player.send_line(f"{Colors.MAGENTA}Spectral chains burst from the ground, binding {target.name}!{Colors.RESET}")
    effects.apply_effect(target, "shackled", 4)
    effects.apply_effect(target, "marked", 8)
    _consume_resources(player, skill)
    return target, True

@register("rotting_touch")
def handle_rotting_touch(player, skill, args, target=None):
    """Setup: [Poisoned] and [Off-Balance]."""
    target = common._get_target(player, args, target, "Infect whom?")
    if not target: return None, True
    
    player.send_line(f"{Colors.GREEN}Your touch infuses {target.name} with sickening decay.{Colors.RESET}")
    effects.apply_effect(target, "poisoned", 4)
    effects.apply_effect(target, "off_balance", 4)
    _consume_resources(player, skill)
    return target, True

@register("deaths_embrace")
def handle_deaths_embrace(player, skill, args, target=None):
    """[V7.2] Payoff/Finisher: massive burst vs Shackled/Bleeding. Logic-Data Wall sync."""
    target = common._get_target(player, args, target, "Unleash the reach of the grave on whom?")
    if not target: return None, True
    
    # 1. Physics Gate
    if not perception.can_see(player, target):
        player.send_line("Target is obscured from the reach of the grave.")
        return None, True

    # [V7.2] Hardcoded multipliers moved to potency_rules in JSON.
    # handle_attack will automatically apply the bonus if [Shackled] or [Bleeding].
    player.send_line(f"{Colors.BOLD}{Colors.BLACK}DEATH'S EMBRACE! Shadows constrict around {target.name}!{Colors.RESET}")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    
    _consume_resources(player, skill)
    return target, True

@register("corpse_explosion")
def handle_corpse_explosion(player, skill, args, target=None):
    """Payoff/AOE: Detonate a body in the room."""
    corpse = next((i for i in player.room.items if isinstance(i, Corpse)), None)
    if not corpse:
        player.send_line("There are no corpses here to detonate.")
        return None, True
        
    player.room.items.remove(corpse)
    player.send_line(f"{Colors.BOLD}{Colors.RED}BOOM! You detonate the remains of {corpse.name}, creating a gore-spray of necrotic energy!{Colors.RESET}")
    player.room.broadcast(f"{Colors.RED}{player.name} detonates a corpse!{Colors.RESET}", exclude_player=player)
    
    for m in player.room.monsters:
        combat.handle_attack(player, m, player.room, player.game, blessing=skill)
        effects.apply_effect(m, "staggered", 2)
        
    _consume_resources(player, skill)
    return None, True

@register("bone_shield")
def handle_bone_shield(player, skill, args, target=None):
    """Defense: Stack-based mitigation."""
    player.send_line(f"{Colors.WHITE}Swirling plates of bone erupt around you.{Colors.RESET}")
    effects.apply_effect(player, "bone_plate", 60)
    
    # [V7.2] Initialize stacks in state
    state = player.ext_state.setdefault('necromancer', {})
    state['bone_plate_stacks'] = 10
    
    _consume_resources(player, skill)
    return None, True

@register("nether_grip")
def handle_nether_grip(player, skill, args, target=None):
    """Mobility: Pull target/self with LoS check."""
    target = common._get_target(player, args, target, "Grip whom?")
    if not target: return None, True
    
    if not perception.can_see(player, target):
        player.send_line("The nether grip find no purchase through the terrain.")
        return None, True

    player.send_line(f"{Colors.MAGENTA}Spectral hands pull you and {target.name} together!{Colors.RESET}")
    effects.apply_effect(target, "pinned", 2)
    _consume_resources(player, skill)
    return target, True

@register("raise_dead")
def handle_raise_dead(player, skill, args, target=None):
    """[V7.2] Utility/Summon: Spawn a follower from a corpse with data persistence."""
    corpse = next((i for i in player.room.items if isinstance(i, Corpse)), None)
    if not corpse:
        player.send_line("There are no corpses here to reanimate.")
        return None, True
        
    entropy = resources.get_resource(player, "entropy")
    if entropy < 5:
        player.send_line(f"You lack the Entropy (5) to bind a spirit to the material plane.")
        return None, True
        
    player.room.items.remove(corpse)
    player.send_line(f"{Colors.BOLD}{Colors.WHITE}ARISE! A skeleton pulls itself from the remains of {corpse.name} to serve you.{Colors.RESET}")
    player.room.broadcast(f"{Colors.WHITE}{player.name} raises a skeleton from a corpse!{Colors.RESET}", exclude_player=player)
    
    # Spawn the entity
    follower = follower_service.spawn_follower(player, "skeleton_minion")
    if follower:
        # [V7.2] Persistence: Store minion data in ext_state
        minion_info = {
            'proto_id': 'skeleton_minion',
            'name': follower.name,
            'hp': follower.hp,
            'max_hp': follower.max_hp,
            'tags': getattr(follower, 'tags', [])
        }
        nec_state = player.ext_state.setdefault('necromancer', {})
        nec_state.setdefault('minion_data', []).append(minion_info)
        
        if follower not in player.minions:
            player.minions.append(follower)
    
    resources.modify_resource(player, "entropy", -5, source="Raise Dead")
    _consume_resources(player, skill)
    return None, True
