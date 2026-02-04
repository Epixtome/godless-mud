import random
from logic import search
from utilities.colors import Colors
from logic.common import find_by_index, get_reverse_direction
from .common import _apply_damage

def handle_shield_bash(player, skill, args):
    # Target required
    target = find_by_index(player.room.monsters + player.room.players, args)
    if not target and player.fighting:
        target = player.fighting
        
    if not target:
        player.send_line("Shield bash whom?")
        return None, True

    # Calculate & Apply Damage First
    from logic.engines import blessings_engine
    power = blessings_engine.MathBridge.calculate_power(skill, player)
    _apply_damage(player, target, power, skill.name)
    
    if target.hp <= 0:
        return None, True

    # Logic: Damage is applied by _execute_skill later, we handle Knockback here
    if player.room.exits:
        direction = random.choice(list(player.room.exits.keys()))
        target_room = player.room.exits[direction]
        
        # Move the target
        if target in player.room.monsters:
            player.room.monsters.remove(target)
            target.room = target_room # Update ref
            target_room.monsters.append(target)
        elif target in player.room.players:
            player.room.players.remove(target)
            target.room = target_room
            target_room.players.append(target)
            target.send_line(f"{Colors.RED}You are bashed into the next room!{Colors.RESET}")
            from logic.actions import information
            information.look(target, "")
            
        player.room.broadcast(f"{player.name} slams their shield into {target.name}, sending them flying {direction}!", exclude_player=player)
        player.send_line(f"You bash {target.name} {direction}!")
        
        # Break combat references in current room since target is gone
        if player.fighting == target:
            player.fighting = None
            player.state = "normal"
            
        return None, True # Target is gone, no further damage application in this room
    else:
        player.send_line(f"You bash {target.name} against the wall! (No exits)")
        return target, False # Fall through to deal damage

def handle_rescue(player, skill, args):
    if not args:
        player.send_line("Rescue whom?")
        return None, True
        
    ally = search.find_living(player.room, args)
    if not ally:
        player.send_line("You don't see them here.")
        return None, None
        
    # Find mobs fighting the ally
    rescued = False
    for mob in player.room.monsters:
        if mob.fighting == ally:
            mob.fighting = player
            if player not in mob.attackers:
                mob.attackers.append(player)
            player.send_line(f"You intervene, drawing {mob.name}'s attention!")
            mob.room.broadcast(f"{player.name} rescues {ally.name} from {mob.name}!", exclude_player=player)
            rescued = True
            
    if not rescued:
        player.send_line(f"{ally.name} is not under attack.")
        
    return None, True

def handle_sunder(player, skill, args):
    if not args:
        player.send_line("Sunder what?")
        return None, True
        
    parts = args.split()
    target_name = parts[0]
    part_name = parts[1] if len(parts) > 1 else None
    
    target = find_by_index(player.room.monsters + player.room.players, target_name)
    if not target:
        player.send_line("You don't see them here.")
        return None, True
        
    if not hasattr(target, 'body_parts') or not target.body_parts:
        player.send_line(f"{target.name} has no weak points to sunder.")
        return None, True
        
    if not part_name:
        player.send_line(f"Sunder which part? ({', '.join(target.body_parts.keys())})")
        return None, True
        
    if part_name not in target.body_parts:
        player.send_line(f"{target.name} does not have a '{part_name}'.")
        return None, True
        
    part = target.body_parts[part_name]
    if part.get('destroyed', False):
        player.send_line(f"The {part_name} is already broken!")
        return None, True
        
    # Calculate Damage
    from logic.engines import blessings_engine, magic_engine
    power = blessings_engine.MathBridge.calculate_power(skill, player)
    
    # Apply to Part
    part['hp'] -= power
    player.send_line(f"You smash {target.name}'s {part_name} for {power} damage!")
    player.room.broadcast(f"{player.name} smashes {target.name}'s {part_name}!", exclude_player=player)
    
    if part['hp'] <= 0:
        part['destroyed'] = True
        part['hp'] = 0
        player.send_line(f"{Colors.YELLOW}You have destroyed {target.name}'s {part_name}!{Colors.RESET}")
        player.room.broadcast(f"{target.name}'s {part_name} shatters!", exclude_player=player)
        
    # Consume resources
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)
    magic_engine.consume_pacing(player, skill)
    
    # Trigger combat
    if not player.fighting:
        player.fighting = target
        player.state = "combat"
    if hasattr(target, 'fighting') and not target.fighting:
        target.fighting = player
        
    return None, True

def handle_pommel_strike(player, skill, args):
    target = find_by_index(player.room.monsters + player.room.players, args) if args else player.fighting
    if target:
        from logic.engines import status_effects_engine
        status_effects_engine.apply_effect(target, "stun", 4)
        player.send_line(f"{Colors.YELLOW}You smash the pommel into {target.name}'s face!{Colors.RESET}")
    return target, False

def handle_trip(player, skill, args):
    target = find_by_index(player.room.monsters + player.room.players, args) if args else player.fighting
    if target:
        from logic.engines import status_effects_engine
        status_effects_engine.apply_effect(target, "stun", 4)
        player.send_line(f"{Colors.YELLOW}You sweep {target.name}'s legs, knocking them down!{Colors.RESET}")
    return target, False

def handle_drag(player, skill, args):
    # Syntax: drag <target> <direction>
    if not args:
        player.send_line("Drag whom where? (Usage: drag <target> <direction>)")
        return None, True
        
    parts = args.split()
    if len(parts) < 2:
        player.send_line("Usage: drag <target> <direction>")
        return None, True
        
    target_name = parts[0]
    direction = parts[1].lower()
    
    target = find_by_index(player.room.monsters + player.room.players, target_name)
    if not target:
        player.send_line("You don't see them here.")
        return None, True
        
    if direction not in player.room.exits:
        player.send_line("You cannot go that way.")
        return None, True
        
    # Move Player
    from logic.actions import movement
    
    # Capture old room to find target later
    old_room = player.room
    
    # Move Player
    movement._move(player, direction)
    
    # Check if player actually moved
    if player.room == old_room:
        return None, True
    
    # Move Target (Force move from old_room)
    if target in old_room.monsters:
        old_room.monsters.remove(target)
        target.room = player.room
        player.room.monsters.append(target)
    elif target in old_room.players:
        old_room.players.remove(target)
        target.room = player.room
        player.room.players.append(target)
        target.send_line(f"{Colors.RED}{player.name} drags you {direction}!{Colors.RESET}")
        from logic.actions import information
        information.look(target, "")
        
    rev_dir = get_reverse_direction(direction)
    arrival_msg = f" in from the {rev_dir}" if rev_dir else " in"
    player.room.broadcast(f"{player.name} drags {target.name}{arrival_msg}.", exclude_player=player)
    
    player.send_line(f"You drag {target.name} with you.")
    
    return None, True

def handle_push(player, skill, args):
    target = find_by_index(player.room.monsters + player.room.players, args) if args else player.fighting
    if not target:
        player.send_line("Push whom?")
        return None, True
        
    if not player.room.exits:
        player.send_line("There is nowhere to push them!")
        return target, False # Fallback to damage
        
    direction = random.choice(list(player.room.exits.keys()))
    target_room = player.room.exits[direction]
    
    if target in player.room.monsters:
        player.room.monsters.remove(target)
        target.room = target_room
        target_room.monsters.append(target)
    elif target in player.room.players:
        player.room.players.remove(target)
        target.room = target_room
        target_room.players.append(target)
        target.send_line(f"{Colors.RED}{player.name} pushes you {direction}!{Colors.RESET}")
        from logic.actions import information
        information.look(target, "")
        
    player.room.broadcast(f"{player.name} pushes {target.name} {direction}!", exclude_player=player)
    player.send_line(f"You push {target.name} {direction}!")
    
    # Stop combat in current room
    if player.fighting == target:
        player.fighting = None
        player.state = "normal"
        
    return None, True

def handle_struggle(player, skill, args):
    # Removes net/web
    removed = []
    if player.status_effects:
        from logic.engines import status_effects_engine
        for eff in ["net", "web", "root", "grapple"]:
            if eff in player.status_effects:
                status_effects_engine.remove_effect(player, eff)
                removed.append(eff)
    
    if removed:
        player.send_line(f"You struggle and break free from: {', '.join(removed)}!")
    else:
        player.send_line("You struggle, but you aren't restrained.")
    return None, True
