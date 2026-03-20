"""
logic/modules/engineer/actions.py
Engineer Skill Handlers: Master of Mechanical Sentinels and Gadgets.
Pillar: Utility Axis, Positional Defense, and Resource Management.
"""
from logic.actions.registry import register
from logic.core import effects, resources, combat
from logic.engines import action_manager, magic_engine
from utilities.colors import Colors
from logic import common

def _consume_resources(player, skill):
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)
    magic_engine.consume_pacing(player, skill)

@register("wrench_strike")
def handle_wrench_strike(player, skill, args, target=None):
    """Setup/Builder: Physical damage and scrap generation."""
    target = common._get_target(player, args, target, "Tighten whose bolts?")
    if not target: return None, True
    
    player.send_line(f"{Colors.YELLOW}You strike {target.name} with a massive wrench, harvesting tech data.{Colors.RESET}")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    resources.modify_resource(player, "tech_scrap", 15, source="Wrench Strike")
    _consume_resources(player, skill)
    return target, True

@register("shock_grenade")
def handle_shock_grenade(player, skill, args, target=None):
    """Setup: [Shocked] applier."""
    player.send_line(f"{Colors.BLUE}You toss a high-voltage grenade into the center of the fray!{Colors.RESET}")
    for m in player.room.monsters:
        effects.apply_effect(m, "shocked", 4)
        effects.apply_effect(m, "staggered", 2)
    _consume_resources(player, skill)
    return None, True

@register("targeted_pheromone")
def handle_targeted_pheromone(player, skill, args, target=None):
    """Setup: [Marked] for turret priority."""
    target = common._get_target(player, args, target, "Tag whom for execution?")
    if not target: return None, True
    
    player.send_line(f"{Colors.CYAN}A burst of specialized pheromones marks {target.name} as a priority target.{Colors.RESET}")
    effects.apply_effect(target, "marked", 10)
    _consume_resources(player, skill)
    return target, True

from logic.core.services import follower_service

@register("autoturret")
def handle_autoturret(player, skill, args, target=None):
    """Payoff/Summon: Deploys a mechanical sentinel structure."""
    scrap = player.resources.get('tech_scrap', 0)
    if scrap < 20:
         player.send_line(f"You need 20 Tech Scrap to assemble a functional turret.")
         return None, True
         
    player.send_line(f"{Colors.BOLD}{Colors.WHITE}Assembling... CLANK! An Automated Sentinel comes online!{Colors.RESET}")
    
    # [V6.5] Deep Implementation: Spawn the physical structure
    turret = follower_service.spawn_follower(player, "engineer_autoturret", entity_type="structure")
    
    if turret:
        player.ext_state['engineer']['active_turret'] = True
        resources.modify_resource(player, "tech_scrap", -20)
        _consume_resources(player, skill)
        return None, True
    else:
        player.send_line("Construction failed: Assembly line obstructed.")
        return None, True

@register("overdrive")
def handle_overdrive(player, skill, args, target=None):
    """Payoff/Burst: massive damage vs staggered/marked. Consumes active turret."""
    if not player.ext_state.get('engineer', {}).get('active_turret'):
         player.send_line(f"You need an active turret to trigger an overdrive!")
         return None, True
         
    player.send_line(f"{Colors.BOLD}{Colors.RED}OVERDRIVE! The turret screams as it ignores all safety limits!{Colors.RESET}")
    
    # [V6.5] Resolve Attacker Source: Damage should come FROM the turret entity
    turret_ent = None
    for m in player.room.monsters:
        if getattr(m, 'owner_id', None) == player.id and getattr(m, 'is_stationary', False):
             turret_ent = m
             break
    
    # Fallback to player if turret object is missing (safety)
    attacker = turret_ent or player
    
    # [V6.5] Owner Protection: Filter targets to exclude own minions/structures
    targets = [m for m in player.room.monsters if m.hp > 0 and getattr(m, 'owner_id', None) != player.id]
    
    for m in targets:
         if effects.has_effect(m, "marked") or effects.has_effect(m, "staggered"):
              attacker.overdrive_multiplier = 3.0
              combat.handle_attack(attacker, m, player.room, player.game, blessing=skill)
              if hasattr(attacker, 'overdrive_multiplier'): del attacker.overdrive_multiplier
         else:
              combat.handle_attack(attacker, m, player.room, player.game, blessing=skill)
    
    # [V6.5] Physical Cleanup: Destroy the actual turret entity
    player.ext_state['engineer']['active_turret'] = False
    if turret_ent:
         follower_service.cleanup_follower(turret_ent)
             
    _consume_resources(player, skill)
    return None, True

@register("portable_barrier")
def handle_portable_barrier(player, skill, args, target=None):
    """Defense: Self-protection and LOS block via structure deployment."""
    scrap = player.resources.get('tech_scrap', 0)
    if scrap < 40:
         player.send_line(f"You need 40 Tech Scrap to deploy a Hard-Light Barrier.")
         return None, True
         
    player.send_line(f"{Colors.CYAN}You deploy a hard-light barrier to anchor your position.{Colors.RESET}")
    
    # [V6.5] Deep Implementation: Spawn the physical barrier structure
    barrier = follower_service.spawn_follower(player, "engineer_barrier", entity_type="structure")
    
    if barrier:
        effects.apply_effect(player, "shielded", 4)
        resources.modify_resource(player, "tech_scrap", -40)
        _consume_resources(player, skill)
        return None, True
    else:
        player.send_line("Deployment failed: Surface too unstable.")
        return None, True

@register("jetpack_boost")
def handle_jetpack_boost(player, skill, args, target=None):
    """Mobility: Leap and fire trail."""
    player.send_line(f"{Colors.BOLD}{Colors.YELLOW}WHOOSH! Your jetpack ignites, scorching the ground beneath you!{Colors.RESET}")
    for m in player.room.monsters:
        if getattr(m, 'owner_id', None) != player.id:
             effects.apply_effect(m, "burning", 2)
    effects.apply_effect(player, "haste", 2)
    _consume_resources(player, skill)
    return None, True

@register("repair_protocol")
def handle_repair_protocol(player, skill, args, target=None):
    """Utility/Heal: Restoration of machines."""
    player.send_line(f"{Colors.BOLD}{Colors.GREEN}Repair bots active! Metal knits back together.{Colors.RESET}")
    target = player
    heal_amt = int(target.max_hp * 0.20)
    target.modify_hp(heal_amt)
    resources.modify_resource(player, "tech_scrap", 30)
    _consume_resources(player, skill)
    return None, True
