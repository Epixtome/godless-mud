"""
logic/modules/beastmaster/actions.py
Beastmaster Skill Handlers: Master of the Wild and Bonded Kill.
Pillar: Utility, Pet Control, and Pack Mitigation.
"""
from logic.actions.registry import register
from logic.core import effects, resources, combat
from logic.engines import action_manager, magic_engine
from utilities.colors import Colors
from logic import common
from logic.core.services import follower_service, world_service

def _consume_resources(player, skill):
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)
    magic_engine.consume_pacing(player, skill)

@register("wild_strike")
def handle_wild_strike(player, skill, args, target=None):
    """Setup/Builder: High-physical damage and Bond generation."""
    target = common._get_target(player, args, target, "Maul whom?")
    if not target: return None, True
    
    player.send_line(f"{Colors.YELLOW}You strike with feral fury, drawing blood and building bond!{Colors.RESET}")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    resources.modify_resource(player, "bond", 5, source="Wild Strike")
    
    _consume_resources(player, skill)
    return target, True

@register("tame_beast")
def handle_tame_beast(player, skill, args, target=None):
    """Deep Taming: Recruit a wild beast into your pack."""
    # [V6.5] World Selection: Identify the wild beast
    target = common._get_target(player, args, target, "Tame which creature?")
    if not target: return None, True
    
    # [V6.5] Faction Check: Must be a beast
    if "beast" not in getattr(target, 'tags', []):
        player.send_line(f"{target.name} resists your spiritual call. It is no mere beast.")
        return None, True
        
    # [V6.5] The GCR Gate (Audit Restriction)
    player_cr = combat.get_combat_rating(player)
    target_cr = combat.get_combat_rating(target)
    
    if player_cr < target_cr:
        player.send_line(f"Your presence (GCR: {player_cr}) fails to intimidate {target.name} (GCR: {target_cr}).")
        player.send_line(f"{Colors.YELLOW}Gear up and increase your Combat Rating to tame this dangerous creature.{Colors.RESET}")
        return None, True
        
    # [V6.5] Pack Limit: Only one beast at a time
    if any(m for m in player.room.monsters if getattr(m, 'owner_id', None) == player.id and "beast" in getattr(m, 'tags', [])):
         player.send_line("Your soul is already bonded to a beast. You cannot handle another.")
         return None, True

    player.send_line(f"{Colors.BOLD}{Colors.CYAN}You focus your will on {target.name}, weaving a primal bond between your souls!{Colors.RESET}")
    
    # [V6.5] Global Binding
    follower_service.bind_follower(player, target)
    
    # Tag as pet for Beastmaster logic
    target.is_pet = True
    target.tamed_name = target.name
    
    # Live Tracking (Transient - not saved to JSON)
    player.active_pet = target
    if target not in player.minions:
        player.minions.append(target)
    
    _consume_resources(player, skill)
    return target, True

@register("intimidating_roar")
def handle_intimidating_roar(player, skill, args, target=None):
    """Setup: [Dazed] for crowd control."""
    player.send_line(f"{Colors.BOLD}{Colors.WHITE}Your companion unleashes a primal roar that echoes through the room!{Colors.RESET}")
    for m in player.room.monsters:
        effects.apply_effect(m, "dazed", 4)
        
    resources.modify_resource(player, "bond", 10, source="Roar")
    _consume_resources(player, skill)
    return None, True

@register("bestial_wrath")
def handle_bestial_wrath(player, skill, args, target=None):
    """Payoff/Burst: massive damage from pet."""
    player.send_line(f"{Colors.BOLD}{Colors.RED}BESTIAL WRATH! Your companion enters a blood-frenzy!{Colors.RESET}")
    bond = player.ext_state.get('beastmaster', {}).get('bond', 0)
    # Multiply pet damage or duration?
    effects.apply_effect(player, "beast_wrath", 10 + (bond // 10))
    resources.modify_resource(player, "bond", -bond)
    
    _consume_resources(player, skill)
    return None, True

@register("coordinated_kill")
def handle_coordinated_kill(player, skill, args, target=None):
    """Finisher: You and pet strike vs marked."""
    target = common._get_target(player, args, target, "Execute the coordinated strike on whom?")
    if not target: return None, True
    
    player.send_line(f"{Colors.BOLD}{Colors.WHITE}COORDINATED KILL! You and your beast strike in perfect harmony!{Colors.RESET}")
    if effects.has_effect(target, "marked"):
        player.coord_multiplier = 4.0
        try:
             combat.handle_attack(player, target, player.room, player.game, blessing=skill)
        finally:
             if hasattr(player, 'coord_multiplier'): del player.coord_multiplier
             
    combat.handle_attack(player, target, player.room, player.game, blessing=skill) # Standard strike
    _consume_resources(player, skill)
    return target, True

@register("pack_bond")
def handle_pack_bond(player, skill, args, target=None):
    """Defense: Shared mitigation."""
    player.send_line(f"{Colors.YELLOW}You enter a symbiotic defense with your companion.{Colors.RESET}")
    effects.apply_effect(player, "pack_bonded", 8) # Logic in combat engine for redirection
    _consume_resources(player, skill)
    return None, True

@register("feral_leap")
def handle_feral_leap(player, skill, args, target=None):
    """Mobility: linear jump and stagger."""
    player.send_line(f"{Colors.WHITE}You and your beast leap through the air!{Colors.RESET}")
    effects.apply_effect(player, "haste", 2)
    _consume_resources(player, skill)
    return None, True

@register("call_companion")
def handle_call_companion(player, skill, args, target=None):
    """Utility/Summon: Call your pet to your side."""
    state = player.ext_state.get('beastmaster', {})
    pet = state.get('active_pet')
    
    if not pet or getattr(pet, 'hp', 0) <= 0:
        player.send_line(f"{Colors.RED}You have no active companion to call.{Colors.RESET}")
        return None, True
        
    if pet.room == player.room:
        player.send_line(f"{getattr(pet, 'tamed_name', pet.name)} is already here.")
        return None, True

    player.send_line(f"{Colors.CYAN}You let out a sharp whistle, calling {getattr(pet, 'tamed_name', pet.name)} to your side!{Colors.RESET}")
    player.room.broadcast(f"{player.name} whistles loudly, and a beast appears!", exclude_player=player)
    
    world_service.move_entity(pet, player.room)
    
    _consume_resources(player, skill)
    return None, True
