"""
logic/modules/beastmaster/actions.py
Beastmaster Skill Handlers: Master of the Wild and Bonded Kill.
V7.2 Standard Refactor (Baking Branch).
"""
import logging
from logic.actions.registry import register
from logic.core import effects, resources, combat, perception
from logic.engines import action_manager, magic_engine
from utilities.colors import Colors
from logic import common
from logic.core.services import follower_service, world_service

logger = logging.getLogger("GodlessMUD")

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
    
    # [V7.2] Bond generation moved to standard resource mod
    resources.modify_resource(player, "bond", 5, source="Wild Strike")
    
    _consume_resources(player, skill)
    return target, True

@register("tame_beast")
def handle_tame_beast(player, skill, args, target=None):
    """[V7.2] Deep Taming: Recruit a wild beast into your pack."""
    target = common._get_target(player, args, target, "Tame which creature?")
    if not target: return None, True
    
    # 1. Physics Gate (Ridge Rule / LoS)
    if not perception.can_see(player, target):
        player.send_line("You cannot bond with a creature you cannot see clearly.")
        return None, True

    # 2. Tag/Logic Gates
    if "beast" not in getattr(target, 'tags', []):
        player.send_line(f"{target.name} resists your spiritual call. It is no mere beast.")
        return None, True
        
    player_cr = combat.get_combat_rating(player)
    target_cr = combat.get_combat_rating(target)
    
    if player_cr < target_cr:
        player.send_line(f"Your presence (GCR: {player_cr}) fails to intimidate {target.name} (GCR: {target_cr}).")
        player.send_line(f"{Colors.YELLOW}Increase your Combat Rating to tame this powerful creature.{Colors.RESET}")
        return None, True
        
    if any(m for m in player.room.monsters if getattr(m, 'owner_id', None) == player.id and "beast" in getattr(m, 'tags', [])):
         player.send_line("Your soul is already bonded to a beast. You cannot handle another.")
         return None, True

    player.send_line(f"{Colors.BOLD}{Colors.CYAN}You focus your will on {target.name}, weaving a primal bond between your souls!{Colors.RESET}")
    
    # 3. Global Binding & Persistence
    follower_service.bind_follower(player, target)
    target.is_pet = True
    target.tamed_name = target.name
    
    # [V7.2] Persistence standard: Store pet data in ext_state
    player.ext_state['beastmaster']['pet_data'] = {
        'proto_id': getattr(target, 'prototype_id', 'wild_beast'),
        'name': target.name,
        'hp': target.hp,
        'max_hp': target.max_hp,
        'tamed_name': target.name
    }
    
    player.active_pet = target # Transient ref
    if target not in player.minions:
        player.minions.append(target)
    
    _consume_resources(player, skill)
    return target, True

@register("intimidating_roar")
def handle_intimidating_roar(player, skill, args, target=None):
    """Setup: [Dazed] for crowd control via pet."""
    pet = next((m for m in player.room.monsters if getattr(m, 'owner_id', None) == player.id and getattr(m, 'is_pet', False)), None)
    if not pet:
        player.send_line("You need an active companion to roar.")
        return None, True

    player.send_line(f"{Colors.BOLD}{Colors.WHITE}Your companion unleashes a primal roar that echoes through the room!{Colors.RESET}")
    for m in player.room.monsters:
        if m != player and m != pet:
            effects.apply_effect(m, "dazed", 4)
        
    resources.modify_resource(player, "bond", 10, source="Roar")
    _consume_resources(player, skill)
    return None, True

@register("bestial_wrath")
def handle_bestial_wrath(player, skill, args, target=None):
    """Payoff/Burst: Logic-Data Wall duration scaling."""
    pet = next((m for m in player.room.monsters if getattr(m, 'owner_id', None) == player.id and getattr(m, 'is_pet', False)), None)
    if not pet:
        player.send_line("You have no companion to empower.")
        return None, True

    player.send_line(f"{Colors.BOLD}{Colors.RED}BESTIAL WRATH! Your companion enters a blood-frenzy!{Colors.RESET}")
    bond = resources.get_resource(player, 'bond')
    
    # [V7.2] Duration scaling moved to JSON rules? Handled here as fallback or primary.
    # In V7.2, we prefer the engine to calculate duration if possible, 
    # but for custom class buffs, we can still use state.
    duration = 10 + (bond // 10)
    effects.apply_effect(pet, "beast_wrath", duration)
    resources.modify_resource(player, "bond", -bond, source="Bestial Wrath Consumption")
    
    _consume_resources(player, skill)
    return None, True

@register("coordinated_kill")
def handle_coordinated_kill(player, skill, args, target=None):
    """[V7.2] Finisher: Synergy strike with Ridge Rule."""
    target = common._get_target(player, args, target, "Execute the coordinated strike on whom?")
    if not target: return None, True
    
    # 1. Physics Gate
    if not perception.can_see(player, target):
        player.send_line("Terrain blocks the line of sight for a coordinated strike.")
        return None, True

    player.send_line(f"{Colors.BOLD}{Colors.WHITE}COORDINATED KILL! You and your beast strike in perfect harmony!{Colors.RESET}")
    
    # [V7.2] Multipliers moved to potency_rules in JSON. 
    # handle_attack will automatically check if target is [Marked].
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    
    _consume_resources(player, skill)
    return target, True

@register("pack_bond")
def handle_pack_bond(player, skill, args, target=None):
    """Defense: Shared mitigation."""
    player.send_line(f"{Colors.YELLOW}You enter a symbiotic defense with your companion.{Colors.RESET}")
    effects.apply_effect(player, "pack_bonded", 8) 
    _consume_resources(player, skill)
    return None, True

@register("feral_leap")
def handle_feral_leap(player, skill, args, target=None):
    """Mobility: linear jump."""
    player.send_line(f"{Colors.WHITE}You and your beast leap through the air!{Colors.RESET}")
    effects.apply_effect(player, "haste", 2)
    _consume_resources(player, skill)
    return None, True

@register("call_companion")
def handle_call_companion(player, skill, args, target=None):
    """[V7.2] Utility: Persistent Pet Summon/Call."""
    bm_state = player.ext_state.get('beastmaster', {})
    pet_data = bm_state.get('pet_data')
    
    # 1. Check for Active Pet in World
    active_pet = next((m for m in player.room.monsters if getattr(m, 'owner_id', None) == player.id and getattr(m, 'is_pet', False)), None)
    
    if active_pet:
        player.send_line(f"{active_pet.name} is already here.")
        return None, True

    if not pet_data:
        player.send_line(f"{Colors.RED}You have no active companion to call. Go tame a beast!{Colors.RESET}")
        return None, True

    player.send_line(f"{Colors.CYAN}You let out a sharp whistle, calling your companion to your side!{Colors.RESET}")
    player.room.broadcast(f"{player.name} whistles loudly, and a beast emerges from the wilds!", exclude_player=player)
    
    # [V7.2] Persistence: Spawn from pet_data
    new_pet = follower_service.spawn_follower(player, pet_data['proto_id'])
    if new_pet:
        new_pet.name = pet_data['name']
        new_pet.hp = pet_data['hp']
        new_pet.max_hp = pet_data['max_hp']
        new_pet.tamed_name = pet_data.get('tamed_name', new_pet.name)
        new_pet.is_pet = True
        player.active_pet = new_pet
        
    _consume_resources(player, skill)
    return None, True
