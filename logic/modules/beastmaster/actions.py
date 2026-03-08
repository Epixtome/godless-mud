"""
logic/modules/beastmaster/actions.py
Commands for the Beastmaster class.
"""
import json
import os
from logic.actions.registry import register
from utilities.colors import Colors

# --- HELPER FUNCTIONS ---

def _get_bm_state(player):
    """Safely retrieves the beastmaster state bucket."""
    if not hasattr(player, 'ext_state'): return None
    return player.ext_state.get('beastmaster')

def _load_pet_archetypes():
    """Loads pet archetypes from the data definition file."""
    path = 'data/definitions/pets.json'
    if not os.path.exists(path):
        return {}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('archetypes', {})
    except Exception as e:
        print(f"Error loading pet archetypes: {e}")
        return {}

def _consume_resources(player, skill):
    """Utility to consume resources and set cooldowns for class skills."""
    from logic.engines import magic_engine
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)
    magic_engine.consume_pacing(player, skill)

# --- SKILL HANDLERS ---

@register("tame")
def handle_tame(player, skill, args, target=None):
    """
    @tame: If target.hp < 5%, add target tags/name to tamed_library.
    """
    if getattr(player, 'active_class', None) != 'beastmaster':
        return False, "Only Beastmasters can tame creatures."

    from logic.common import _get_target
    target = _get_target(player, args, target, "Tame what?")
    if not target: return None, True
    
    # Generic beast check? Or any mob? The prompt says "If target.hp < 5%, add target tags/name to tamed_library"
    if not hasattr(target, 'hp') or not hasattr(target, 'max_hp'):
        player.send_line(f"{Colors.RED}That creature cannot be tamed.{Colors.RESET}")
        return None, True
        
    hp_percent = (target.hp / target.max_hp) * 100
    if hp_percent > 5.0:
        player.send_line(f"{Colors.YELLOW}{target.name} is too strong to be tamed! Weaken it more! (Current: {int(hp_percent)}%){Colors.RESET}")
        return None, True

    # Success!
    bm_state = _get_bm_state(player)
    if not bm_state: return False, "Beastmaster state not initialized."

    # Determine archetype based on tags (simple mapping)
    archetype = "sentinel" # Default
    tags = getattr(target, 'tags', [])
    if any(t in tags for t in ['tough', 'armored', 'large', 'tank']):
        archetype = "bulwark"
    elif any(t in tags for t in ['fierce', 'fast', 'sharp', 'predator']):
        archetype = "predator"
        
    pet_entry = {
        "name": target.name,
        "archetype": archetype,
        "tags": list(tags)
    }
    
    bm_state['tamed_library'].append(pet_entry)
    player.send_line(f"{Colors.GREEN}You successfully tame {target.name}! It has been added to your library as a {archetype}.{Colors.RESET}")
    player.room.broadcast(f"{player.name} performs a ritual of taming on {target.name}!", exclude_player=player)
    
    # Remove the target mob from the room (it's now yours)
    if target in player.room.monsters:
        player.room.monsters.remove(target)
    
    _consume_resources(player, skill)
    return target, True

@register("call")
def handle_call(player, skill, args, target=None):
    """
    @call <name>: Spawns pet from library. Set sync = 0.
    """
    if getattr(player, 'active_class', None) != 'beastmaster':
        return False, "Only Beastmasters can call pets."

    if not args:
        return False, "Usage: @call <pet_name>"

    bm_state = _get_bm_state(player)
    if not bm_state: return False, "Beastmaster state not initialized."

    # Find the pet in the library
    pet_name = args.strip().lower()
    pet_data = None
    for entry in bm_state['tamed_library']:
        if entry['name'].lower() == pet_name:
            pet_data = entry
            break
            
    if not pet_data:
        player.send_line(f"{Colors.RED}You don't have a tamed pet named '{args}'.{Colors.RESET}")
        return None, True

    # 1. Late Import as per instructions
    from logic.modules.beastmaster.pet import Pet
    
    # 2. Dismiss existing pet if any
    if bm_state['active_pet_uuid']:
        pet_dismissed = False
        # Optimization: Check local room first
        for mob in list(player.room.monsters):
            if getattr(mob, 'owner_id', None) == player.id:
                player.room.monsters.remove(mob)
                player.room.broadcast(f"{mob.name} retreats to the shadows.")
                pet_dismissed = True
                break
        
        if not pet_dismissed:
            for room in player.game.world.rooms.values():
                for mob in list(room.monsters):
                    if getattr(mob, 'owner_id', None) == player.id:
                        room.monsters.remove(mob)
                        room.broadcast(f"{mob.name} retreats to the shadows.")
                    
    # 3. Instantiate and spawn
    archetypes = _load_pet_archetypes()
    arch_meta = archetypes.get(pet_data['archetype'], archetypes.get('sentinel', {}))
    # Add the key into metadata for the class
    arch_meta['key'] = pet_data['archetype']
    
    new_pet = Pet(player, pet_data['name'], arch_meta)
    new_pet.room = player.room
    player.room.monsters.append(new_pet)
    
    bm_state['active_pet_uuid'] = new_pet.id
    bm_state['sync'] = 0 # Fresh call
    
    player.room.broadcast(f"{player.name} whistles, and a {new_pet.name} arrives from the shadows.", exclude_player=player)
    
    _consume_resources(player, skill)
    return new_pet, True

@register("order")
def handle_order(player, skill, args, target=None):
    """
    @order <action>: Commands the active pet.
    """
    if getattr(player, 'active_class', None) != 'beastmaster':
        return False, "Only Beastmasters can order pets."

    if not args:
        return False, "Usage: @order <attack|special|unleash|guard>"

    bm_state = _get_bm_state(player)
    if not bm_state: return False, "Beastmaster state not initialized."
    
    active_pet = None
    for mob in player.room.monsters:
        if getattr(mob, 'owner_id', None) == player.id:
            active_pet = mob
            break
            
    if not active_pet:
        player.send_line(f"{Colors.RED}You don't have an active pet in this room!{Colors.RESET}")
        return None, True

    subcmd = args.split()[0].lower()
    
    if subcmd == "attack":
        # Order pet to attack player's target
        if player.fighting:
            active_pet.fighting = player.fighting
            player.send_line(f"You point at {player.fighting.name}, and {active_pet.name} lunges forward!")
        else:
            player.send_line("Attack what?")
            
    elif subcmd == "special":
        if bm_state['sync'] < 25:
            player.send_line(f"{Colors.RED}Not enough Sync! (Requires 25, have {bm_state['sync']}){Colors.RESET}")
            return None, True
        
        bm_state['sync'] -= 25
        player.send_line(f"You gesture sharply. {active_pet.name} executes a specialized maneuver!")
        # Logic Hook for Archetype Status (implementation depends on effects engine)
        from logic.core import status_effects_engine
        archetypes = _load_pet_archetypes()
        arch_data = archetypes.get(active_pet.archetype_key, {})
        status_id = arch_data.get('special', 'stun')
        
        if active_pet.fighting:
            status_effects_engine.apply_effect(active_pet.fighting, status_id, 2)
            player.send_line(f"{active_pet.fighting.name} is now {status_id.upper()}!")
            
    elif subcmd == "unleash":
        if bm_state['sync'] < 100:
            player.send_line(f"{Colors.RED}Sync not ready! (Requires 100, have {bm_state['sync']}){Colors.RESET}")
            return None, True
            
        bm_state['sync'] = 0
        player.send_line(f"{Colors.BOLD}{Colors.YELLOW}UNLEASH THE BEAST!{Colors.RESET}")
        # Final damage logic...
        if active_pet.fighting:
            from logic.core import resource_engine
            resource_engine.modify_resource(active_pet.fighting, "hp", -50, source=active_pet.name, context="Unleash")
            player.send_line(f"{active_pet.name} tears into {active_pet.fighting.name} with primal fury!")

    elif subcmd == "guard":
        bm_state['order_guard'] = not bm_state['order_guard']
        status = "now guarding" if bm_state['order_guard'] else "no longer guarding"
        player.send_line(f"{active_pet.name} is {status} you.")
    
    else:
        player.send_line(f"{Colors.YELLOW}Unknown order: {subcmd}. Use: attack, special, unleash, or guard.{Colors.RESET}")
        return None, True
        
    _consume_resources(player, skill)
    return active_pet, True

@register("whistle")
def handle_whistle(player, skill, args, target=None):
    """
    @whistle: Teleport pet to player XYZ.
    """
    if getattr(player, 'active_class', None) != 'beastmaster':
        return False, "Only Beastmasters can whistle for pets."

    bm_state = _get_bm_state(player)
    if not bm_state: return False, "Beastmaster state not initialized."

    # Find the pet anywhere in the world
    pet_obj = None
    for room in player.game.world.rooms.values():
        for mob in room.monsters:
            if getattr(mob, 'owner_id', None) == player.id:
                pet_obj = mob
                break
        if pet_obj: break
        
    if not pet_obj:
        player.send_line(f"{Colors.RED}You have no active pet to whistle for.{Colors.RESET}")
        return None, True
        
    # Teleport
    if pet_obj.room:
        pet_obj.room.monsters.remove(pet_obj)
        pet_obj.room.broadcast(f"{pet_obj.name} hears a whistle and vanishes.")
        
    pet_obj.room = player.room
    player.room.monsters.append(pet_obj)
    player.room.broadcast(f"{pet_obj.name} leaps from the shadows to {player.name}'s side.")
    player.send_line(f"You whistle sharply, and {pet_obj.name} appears!")
    
    _consume_resources(player, skill)
    return pet_obj, True

@register("pets")
def handle_pets(player, skill, args, target=None):
    """
    @pets: Lists the player's tamed library.
    """
    if getattr(player, 'active_class', None) != 'beastmaster':
        return False, "Only Beastmasters can view their pet library."

    bm_state = _get_bm_state(player)
    if not bm_state: return False, "Beastmaster state not initialized."

    if not bm_state['tamed_library']:
        player.send_line("Your pet library is empty. Go out and tame some creatures!")
        return None, True

    # Header
    player.send_line(f"\n{Colors.BOLD}{Colors.YELLOW}=== Your Tamed Creatures ==={Colors.RESET}")
    
    # Attempt to find active pet name in the current room for the [ACTIVE] tag
    active_pet_name = None
    if bm_state.get('active_pet_uuid'):
        for mob in player.room.monsters:
            if getattr(mob, 'owner_id', None) == player.id:
                active_pet_name = mob.name
                break
    
    for i, pet in enumerate(bm_state['tamed_library'], 1):
        is_active = (pet['name'] == active_pet_name)
        status = f" {Colors.GREEN}[ACTIVE]{Colors.RESET}" if is_active else ""
        tags_str = f" {Colors.dGREY}[{', '.join(pet.get('tags', []))}]{Colors.RESET}" if pet.get('tags') else ""
        player.send_line(f"{i}. {Colors.CYAN}{pet['name']}{Colors.RESET} ({pet['archetype'].title()}){tags_str}{status}")
    
    player.send_line(f"\n{Colors.YELLOW}Total: {len(bm_state['tamed_library'])} / 10{Colors.RESET}")
    player.send_line(f"Use '{Colors.BOLD}call <name>{Colors.RESET}' to summon a pet.")
    
    return None, True
