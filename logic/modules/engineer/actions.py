"""
logic/modules/engineer/actions.py
Engineer Skill Handlers: Master of Mechanical Sentinels and Gadgets.
V7.2 Standard Refactor (Baking Branch).
"""
import logging
from logic.actions.registry import register
from logic.core import effects, resources, combat, perception
from logic.engines import action_manager, magic_engine
from logic.core.services import follower_service
from utilities.colors import Colors
from logic import common

logger = logging.getLogger("GodlessMUD")

def _consume_resources(player, skill):
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)
    magic_engine.consume_pacing(player, skill)

@register("wrench_strike")
def handle_wrench_strike(player, skill, args, target=None):
    """[V7.2] Setup/Builder: Physical damage and scrap generation with Ridge Rule."""
    target = common._get_target(player, args, target, "Tighten whose bolts?")
    if not target: return None, True
    
    # 1. Physics Gate (Ridge Rule)
    if not perception.can_see(player, target):
        player.send_line("Terrain blocks your wrench from reaching the target.")
        return None, True

    player.send_line(f"{Colors.YELLOW}You strike {target.name} with a massive wrench, harvesting tech data.{Colors.RESET}")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    
    # [V7.2] URM Generation: Tech Scrap
    resources.modify_resource(player, "tech_scrap", 15, source="Wrench Strike")
    
    _consume_resources(player, skill)
    return target, True

@register("shock_grenade")
def handle_shock_grenade(player, skill, args, target=None):
    """[V7.2] Setup: AOE CC with Ridge Rule check."""
    player.send_line(f"{Colors.BLUE}You toss a high-voltage grenade into the center of the fray!{Colors.RESET}")
    
    for m in player.room.monsters:
        if perception.can_see(player, m):
            effects.apply_effect(m, "shocked", 4)
            effects.apply_effect(m, "staggered", 2)
            
    _consume_resources(player, skill)
    return None, True

@register("targeted_pheromone")
def handle_targeted_pheromone(player, skill, args, target=None):
    """[V7.2] Setup: [Marked] with Ridge Rule."""
    target = common._get_target(player, args, target, "Tag whom for execution?")
    if not target: return None, True
    
    if not perception.can_see(player, target):
        player.send_line("The pheromone cloud fails to penetrate the terrain.")
        return None, True

    player.send_line(f"{Colors.CYAN}A burst of specialized pheromones marks {target.name} as a priority target.{Colors.RESET}")
    effects.apply_effect(target, "marked", 10)
    _consume_resources(player, skill)
    return target, True

@register("autoturret")
def handle_autoturret(player, skill, args, target=None):
    """[V7.2] Payoff/Summon: Deploys a mechanical sentinel structure via Follower Standard."""
    scrap = resources.get_resource(player, 'tech_scrap')
    if scrap < 20:
         player.send_line(f"You need 20 Tech Scrap to assemble a functional turret (You have {scrap}).")
         return None, True
         
    player.send_line(f"{Colors.BOLD}{Colors.WHITE}Assembling... CLANK! An Automated Sentinel comes online!{Colors.RESET}")
    
    # [V7.2] Deep Implementation: Spawn structure using follower_service
    turret = follower_service.spawn_follower(player, "engineer_autoturret", entity_type="structure")
    
    if turret:
        # Link for state tracking
        player.ext_state['engineer'].setdefault('active_constructs', []).append(turret.id)
        
        # [V7.2] Consumption via URM
        resources.modify_resource(player, "tech_scrap", -20, source="Construction Cost")
        _consume_resources(player, skill)
        return None, True
    else:
        player.send_line("Construction failed: Assembly line obstructed by terrain.")
        return None, True

@register("overdrive")
def handle_overdrive(player, skill, args, target=None):
    """[V7.2] Payoff/Burst: Logic-Data Wall sync via constructs."""
    construct_ids = player.ext_state.get('engineer', {}).get('active_constructs', [])
    if not construct_ids:
          player.send_line(f"You need active constructs to trigger an overdrive!")
          return None, True
         
    player.send_line(f"{Colors.BOLD}{Colors.RED}OVERDRIVE! Your machinery screams as it ignores all safety limits!{Colors.RESET}")
    
    # Locate turret in the room
    turret_ent = None
    for m in player.room.monsters:
        if m.id in construct_ids and getattr(m, 'is_stationary', False):
             turret_ent = m
             break
    
    attacker = turret_ent or player
    
    # Filter targets
    targets = [m for m in player.room.monsters if m.hp > 0 and getattr(m, 'owner_id', None) != player.id]
    
    for m in targets:
         if perception.can_see(attacker, m):
              # [V7.2] Multipliers handled in JSON potency_rules
              if effects.has_effect(m, "marked") or effects.has_effect(m, "staggered"):
                   player.send_line(f"{Colors.YELLOW}Turret sensors lock on to {m.name}'s weak points!{Colors.RESET}")
              
              combat.handle_attack(attacker, m, player.room, player.game, blessing=skill)
    
    # [V7.2] Cleanup constructs after overdrive (consumes them)
    if turret_ent:
         follower_service.cleanup_follower(turret_ent)
         player.ext_state['engineer']['active_constructs'].remove(turret_ent.id)
              
    _consume_resources(player, skill)
    return None, True

@register("portable_barrier")
def handle_portable_barrier(player, skill, args, target=None):
    """[V7.2] Defense: Tactical structure deployment."""
    scrap = resources.get_resource(player, 'tech_scrap')
    if scrap < 40:
         player.send_line(f"You need 40 Tech Scrap to deploy a Hard-Light Barrier.")
         return None, True
         
    player.send_line(f"{Colors.CYAN}You deploy a hard-light barrier to anchor your position.{Colors.RESET}")
    
    barrier = follower_service.spawn_follower(player, "engineer_barrier", entity_type="structure")
    
    if barrier:
        player.ext_state['engineer'].setdefault('active_constructs', []).append(barrier.id)
        effects.apply_effect(player, "shielded", 6)
        
        # [V7.2] Consumption via URM
        resources.modify_resource(player, "tech_scrap", -40, source="Deployment Cost")
        _consume_resources(player, skill)
        return None, True
    else:
        player.send_line("Deployment failed: Surface too unstable.")
        return None, True

@register("jetpack_boost")
def handle_jetpack_boost(player, skill, args, target=None):
    """[V7.2] Mobility: Leap and damage."""
    player.send_line(f"{Colors.BOLD}{Colors.YELLOW}WHOOSH! Your jetpack ignites!{Colors.RESET}")
    for m in player.room.monsters:
        if getattr(m, 'owner_id', None) != player.id and perception.can_see(player, m):
             effects.apply_effect(m, "burning", 2)
             
    effects.apply_effect(player, "haste", 2)
    _consume_resources(player, skill)
    return None, True

@register("repair_protocol")
def handle_repair_protocol(player, skill, args, target=None):
    """[V7.2] Utility/Heal: Restoration via scrap."""
    player.send_line(f"{Colors.BOLD}{Colors.GREEN}Repair bots active! Metal knits back together.{Colors.RESET}")
    
    # Heal via URM for consistency
    heal_amt = int(player.max_hp * 0.20)
    resources.modify_resource(player, "hp", heal_amt, source="Repair Bots", context="Techno-Restoration")
    
    # Gain scrap if physiology bonus? Or just fixed.
    resources.modify_resource(player, "tech_scrap", 30, source="Scrap Reclamation")
    
    _consume_resources(player, skill)
    return None, True
