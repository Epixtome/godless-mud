"""
logic/modules/beastmaster/events.py
Event subscriptions for the Beastmaster class (V6.5 Update).
Decoupled logic that hooks into core engine events.
"""
from logic.core import event_engine, effects, resources, follower_service
from logic.core.services import world_service
from utilities.colors import Colors

def _get_active_pet(player):
    """Safely retrieves the active pet in the same room as the player."""
    # Check for the pet in the room's monsters list that belongs to the player
    if not player.room: return None
    for mob in player.room.monsters:
        if getattr(mob, 'owner_id', None) == player.id and getattr(mob, 'is_pet', False):
            return mob
    return None

def on_take_damage(ctx):
    """
    Event Handler: Damage Redirection (Pack Mitigation).
    If bond > 50 and pack_bonded effect is active, redirect 70% damage to active_pet.
    """
    target = ctx.get('target')
    damage = ctx.get('damage', 0)
    
    if getattr(target, 'active_class', None) != 'beastmaster':
        return

    bm_state = target.ext_state.get('beastmaster', {})
    if not effects.has_effect(target, 'pack_bonded'):
        return
        
    if bm_state.get('bond', 0) < 50:
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
    Event Handler: Bond management.
    If Player/Pet in same room: bond += 5 (Up to 100).
    If Player/Pet in different rooms: bond -= 10.
    """
    player = ctx.get('player')
    if not player or getattr(player, 'active_class', None) != 'beastmaster':
        return
        
    bm_state = player.ext_state.get('beastmaster', {})
    
    # Find active pet object by room search or transient reference
    pet = getattr(player, 'active_pet', None)
    if not pet or getattr(pet, 'hp', 0) <= 0:
        # Fallback search if pet object is transient
        pet = _get_active_pet(player)
        if pet: player.active_pet = pet # Re-establish link
        
    if not pet:
        # Gradually lose bond if no pet is active
        resources.modify_resource(player, 'bond', -5, source="Neglect")
        return
        
    # Same room check
    if hasattr(pet, 'room') and pet.room == player.room:
        resources.modify_resource(player, 'bond', 5, source="Proximity")
    else:
        resources.modify_resource(player, 'bond', -10, source="Distance")

def on_death_cleanup(ctx):
    """
    Event Handler: Handle pet death.
    Apply [Heartbroken] status to player (STM regen -50% for 60s).
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
        effects.apply_effect(owner, "heartbroken", 60) # High duration debuff
        
        if hasattr(owner, 'active_pet'):
            owner.active_pet = None # Clear active ref
        resources.modify_resource(owner, 'bond', -50, source="Heartbroken")

def on_build_prompt(ctx):
    """
    Event Handler: Injects Beastmaster UI into the prompt.
    [HP/STM | PET: Rex (50/100) | BOND: 80/100]
    """
    player = ctx.get('player')
    prompts = ctx.get('prompts')
    
    if getattr(player, 'active_class', None) != 'beastmaster':
        return
        
    bm_state = player.ext_state.get('beastmaster', {})
    bond = bm_state.get('bond', 0)
    pet = _get_active_pet(player)
    
    if pet:
        name = getattr(pet, 'tamed_name', pet.name)
        pet_info = f"{Colors.YELLOW}PET: {name} ({int(pet.hp)}/{int(pet.max_hp)}){Colors.RESET}"
    else:
        pet_info = f"{Colors.RED}PET: None{Colors.RESET}"
        
    bond_color = Colors.GREEN if bond >= 80 else Colors.YELLOW if bond >= 40 else Colors.RED
    prompts.append(f"{pet_info} | {bond_color}BOND: {bond}%{Colors.RESET}")

def on_after_move(ctx):
    """
    Event Handler: Pet Follow logic.
    When a Beastmaster moves, their pet stays by their side.
    """
    player = ctx.get('player')
    new_room = ctx.get('new_room')
    old_room = ctx.get('old_room')
    
    if not player or getattr(player, 'active_class', None) != 'beastmaster':
        return

    # Find pet in old room
    pet = None
    for mob in old_room.monsters:
        if getattr(mob, 'owner_id', None) == player.id and getattr(mob, 'is_pet', False):
            pet = mob
            break
            
    if pet:
        # Service-based movement ensures registry consistency
        world_service.move_entity(pet, new_room)
        new_room.broadcast(f"{getattr(pet, 'tamed_name', pet.name)} follows {player.name}.")

def on_combat_hit_assist(ctx):
    """
    Event Handler: Pet Assist logic.
    When a Beastmaster strikes a target, their pet engages as well.
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
