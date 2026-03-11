"""
logic/modules/beastmaster/events.py
Event subscriptions for the Beastmaster class.
Decoupled logic that hooks into core engine events.
"""
from logic.core import event_engine, effects, resources
from utilities.colors import Colors

def _get_active_pet(player):
    """Safely retrieves the active pet in the same room as the player."""
    if not player.room: return None
    for mob in player.room.monsters:
        if getattr(mob, 'owner_id', None) == player.id:
            return mob
    return None

def on_take_damage(ctx):
    """
    Event Handler: Damage Redirection.
    If sync > 50 and order_guard is active, redirect 70% damage to active_pet.
    """
    target = ctx.get('target')
    damage = ctx.get('damage', 0)
    
    if getattr(target, 'active_class', None) != 'beastmaster':
        return

    bm_state = target.ext_state.get('beastmaster')
    if not bm_state or not bm_state.get('order_guard'):
        return
        
    if bm_state['sync'] < 50:
        return
        
    pet = _get_active_pet(target)
    if not pet or pet.hp <= 0:
        return
        
    # Redirect 70%
    redirected = int(damage * 0.7)
    target_damage = damage - redirected
    
    # Apply redirected damage to pet
    resources.modify_resource(pet, "hp", -redirected, source=target.name, context="Guarded")
    
    # Update context for the original damage calculation
    ctx['damage'] = target_damage
    target.send_line(f"{Colors.GREEN}[GUARD] {pet.name} intercepts {redirected} damage for you!{Colors.RESET}")

def on_combat_tick(ctx):
    """
    Event Handler: Sync management.
    If Player/Pet in same room: sync += 5.
    If Player/Pet in different rooms: sync -= 10.
    """
    player = ctx.get('player')
    if not player or getattr(player, 'active_class', None) != 'beastmaster':
        return
        
    bm_state = player.ext_state.get('beastmaster')
    if not bm_state: return
    
    # Find pet
    pet = None
    for room in player.game.world.rooms.values():
        for mob in room.monsters:
            if getattr(mob, 'owner_id', None) == player.id:
                pet = mob
                break
        if pet: break
        
    if not pet:
        # Gradually lose sync if no pet is active
        bm_state['sync'] = max(0, bm_state['sync'] - 5)
        return
        
    # Same room check
    if pet.room == player.room:
        bm_state['sync'] = min(100, bm_state['sync'] + 5)
    else:
        bm_state['sync'] = max(0, bm_state['sync'] - 10)

def on_pet_death(ctx):
    """
    Event Handler: Handle pet death.
    Apply [Heartbroken] status to player (STM regen -50% for 60s).
    """
    mob = ctx.get('mob')
    if not getattr(mob, 'is_pet', False):
        return
        
    owner_id = getattr(mob, 'owner_id', None)
    if not owner_id: return
    
    owner = mob.game.players.get(owner_id) if mob.game else None
    if owner:
        owner.send_line(f"{Colors.BOLD}{Colors.RED}Your heart shatters as {mob.name} falls!{Colors.RESET}")
        effects.apply_effect(owner, "heartbroken", 60) # 30 ticks (60s)
        
        bm_state = owner.ext_state.get('beastmaster')
        if bm_state:
            bm_state['active_pet_uuid'] = None
            bm_state['sync'] = 0

def on_build_prompt(ctx):
    """
    Event Handler: Injects Beastmaster UI into the prompt.
    [HP/STM | PET: Rex (50 HP) | SYNC: 100]
    """
    player = ctx.get('player')
    prompts = ctx.get('prompts')
    
    if getattr(player, 'active_class', None) != 'beastmaster':
        return
        
    bm_state = player.ext_state.get('beastmaster')
    if not bm_state: return
    
    sync = bm_state.get('sync', 0)
    pet = _get_active_pet(player)
    
    if pet:
        pet_info = f"{Colors.YELLOW}PET: {pet.tamed_name} ({pet.hp}/{pet.max_hp}){Colors.RESET}"
    else:
        pet_info = f"{Colors.RED}PET: None{Colors.RESET}"
        
    sync_color = Colors.GREEN if sync >= 100 else Colors.CYAN
    prompts.append(f"{pet_info} | {sync_color}SYNC: {sync}{Colors.RESET}")

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
        if getattr(mob, 'owner_id', None) == player.id:
            pet = mob
            break
            
    if pet:
        if pet in old_room.monsters:
            old_room.monsters.remove(pet)
        if pet not in new_room.monsters:
            new_room.monsters.append(pet)
        pet.room = new_room
        new_room.broadcast(f"{pet.name} follows {player.name}.")

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
        attacker.send_line(f"{pet.name} sees you strike and leaps into the fray!")

def register_events():
    # Subscribe to global engine events
    event_engine.subscribe("on_take_damage", on_take_damage)
    event_engine.subscribe("on_combat_tick", on_combat_tick) 
    event_engine.subscribe("on_mob_death", on_pet_death) 
    event_engine.subscribe("on_build_prompt", on_build_prompt)
    event_engine.subscribe("after_move", on_after_move)
    event_engine.subscribe("on_combat_hit", on_combat_hit_assist)
