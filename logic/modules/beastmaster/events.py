"""
logic/modules/beastmaster/events.py
Event subscriptions for the Beastmaster class (V7.2 Sync).
Decoupled logic that hooks into core engine events.
"""
import logging
from logic.core import event_engine, effects, resources, follower_service
from logic.core.services import world_service
from utilities.colors import Colors

logger = logging.getLogger("GodlessMUD")

def _get_active_pet(player):
    """Safely retrieves the active pet in the same room as the player."""
    if not player.room: return None
    for mob in player.room.monsters:
        if getattr(mob, 'owner_id', None) == player.id and getattr(mob, 'is_pet', False):
            return mob
    return None

def on_take_damage(ctx):
    """
    [V7.2] Event Handler: Damage Redirection (Pack Mitigation).
    If bond > 50 and pack_bonded effect is active, redirect 70% damage to active_pet.
    """
    target = ctx.get('target')
    damage = ctx.get('damage', 0)
    
    if getattr(target, 'active_class', None) != 'beastmaster':
        return

    # [V7.2] URM resource check
    bond = resources.get_resource(target, 'bond')
    if not effects.has_effect(target, 'pack_bonded') or bond < 50:
        return
        
    pet = _get_active_pet(target)
    if not pet or getattr(pet, 'hp', 0) <= 0:
        return
        
    # Redirect 70%
    redirected = int(damage * 0.7)
    target_damage = damage - redirected
    
    # Apply redirected damage to pet via resources facade
    resources.modify_resource(pet, "hp", -redirected, source=target.name, context="Guarded strike")
    
    # Update context for the original damage calculation
    ctx['damage'] = target_damage
    if hasattr(target, 'send_line'):
        target.send_line(f"{Colors.GREEN}[BOND] {getattr(pet, 'tamed_name', pet.name)} intercepts {redirected} damage for you!{Colors.RESET}")

def on_combat_tick(ctx):
    """
    [V7.2] Event Handler: Bond management.
    Handles proximity bond gain/loss and data persistence updates.
    """
    player = ctx.get('player')
    if not player or getattr(player, 'active_class', None) != 'beastmaster':
        return
        
    # 1. Proximity Check
    pet = _get_active_pet(player)
    if not pet:
        resources.modify_resource(player, 'bond', -5, source="Neglect")
        return
        
    # 2. Persistence Update (V7.2 State-Data Wall)
    # Ensure current pet HP is written to the player snapshot
    bm_state = player.ext_state.setdefault('beastmaster', {})
    if 'pet_data' in bm_state and bm_state['pet_data']:
        bm_state['pet_data']['hp'] = pet.hp
        bm_state['pet_data']['max_hp'] = pet.max_hp

    # 3. Same room check
    if hasattr(pet, 'room') and pet.room == player.room:
        resources.modify_resource(player, 'bond', 5, source="Proximity")
    else:
        resources.modify_resource(player, 'bond', -10, source="Distance")

def on_death_cleanup(ctx):
    """
    [V7.2] Event Handler: Handle pet death.
    Clears pet_data and applies Heartbroken debuff.
    """
    victim = ctx.get('victim')
    if not victim or not getattr(victim, 'is_pet', False):
        return
        
    owner_id = getattr(victim, 'owner_id', None)
    if not owner_id: return
    
    game = getattr(victim, 'game', None)
    owner = game.players.get(owner_id) if game else None
    
    if owner:
        owner.send_line(f"{Colors.BOLD}{Colors.RED}Your heart shatters as {getattr(victim, 'tamed_name', victim.name)} falls!{Colors.RESET}")
        effects.apply_effect(owner, "heartbroken", 60)
        
        # [V7.2] Persistence update
        bm_state = owner.ext_state.setdefault('beastmaster', {})
        bm_state['pet_data'] = None 
        
        resources.modify_resource(owner, 'bond', -50, source="Heartbroken")

def on_build_prompt(ctx):
    """
    [V7.2] Event Handler: Custom Beastmaster HUD.
    Injects pet health status alongside the standard URM prompts.
    """
    player = ctx.get('player')
    prompts = ctx.get('prompts')
    
    if getattr(player, 'active_class', None) != 'beastmaster':
        return
        
    pet = _get_active_pet(player)
    if pet:
        name = getattr(pet, 'tamed_name', pet.name)
        pet_info = f"{Colors.YELLOW}PET: {name} ({int(pet.hp)}/{int(pet.max_hp)}){Colors.RESET}"
        prompts.append(pet_info)

def on_after_move(ctx):
    """
    [V7.2] Event Handler: Pet Follow logic.
    Pet stays by their side when the player moves between rooms.
    """
    player = ctx.get('player')
    new_room = ctx.get('new_room')
    old_room = ctx.get('old_room')
    
    if not player or getattr(player, 'active_class', None) != 'beastmaster':
        return

    pet = _get_active_pet(player)
    if pet and pet.room == old_room:
        world_service.move_entity(pet, new_room)
        new_room.broadcast(f"{getattr(pet, 'tamed_name', pet.name)} follows {player.name}.")

def on_combat_hit_assist(ctx):
    """
    [V7.2] Event Handler: Pet Assist logic.
    Pet engages the same target as the master.
    """
    attacker = ctx.get('attacker')
    target = ctx.get('target')
    
    if not attacker or getattr(attacker, 'active_class', None) != 'beastmaster':
        return
        
    pet = _get_active_pet(attacker)
    if pet and not pet.fighting and target and target.hp > 0:
        pet.fighting = target
        if hasattr(attacker, 'send_line'):
            attacker.send_line(f"{Colors.YELLOW}{getattr(pet, 'tamed_name', pet.name)} sees you strike and leaps into the fray!{Colors.RESET}")

def register_events():
    # Subscribe to global engine events
    event_engine.subscribe("on_calculate_mitigation", on_take_damage)
    event_engine.subscribe("on_combat_tick", on_combat_tick) 
    event_engine.subscribe("on_death", on_death_cleanup) 
    event_engine.subscribe("on_build_prompt", on_build_prompt)
    event_engine.subscribe("after_move", on_after_move)
    event_engine.subscribe("on_combat_hit", on_combat_hit_assist)
