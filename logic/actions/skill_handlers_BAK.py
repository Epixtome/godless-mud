import random
from logic.engines import blessings_engine, magic_engine, status_effects_engine, combat_processor
from logic import mob_manager, search
from utilities.colors import Colors
from utilities import combat_formatter
from logic.common import find_by_index, get_reverse_direction
from models import Corpse, Monster, Player

# --- Private Helpers ---

def _apply_damage(attacker, target, damage, source_name):
    # Apply Defense
    defense = 0
    if hasattr(target, 'get_defense'):
        defense = target.get_defense()
    elif hasattr(target, 'equipped_armor') and target.equipped_armor:
        defense = target.equipped_armor.defense
    
    # Apply Body Part Multipliers (e.g. Broken Shell)
    multiplier = 1.0
    if hasattr(target, 'get_damage_modifier'):
        multiplier = target.get_damage_modifier()

    final_damage = max(1, int((damage - defense) * multiplier))
    target.hp -= final_damage
    
    # Messaging
    att_msg, tgt_msg, _ = combat_formatter.format_damage(attacker.name, target.name, final_damage, source=source_name)
    attacker.send_line(att_msg)
    if hasattr(target, 'send_line'):
        target.send_line(tgt_msg)
        
    # Death Check (Simplified, relies on next heartbeat to clean up corpse usually, 
    # but we can trigger death logic here if we want instant feedback)
    if target.hp <= 0:
        attacker.send_line(f"{Colors.BOLD}{Colors.YELLOW}You have defeated {target.name}!{Colors.RESET}")
        # Execute death logic immediately
        if isinstance(target, Monster):
            combat_processor.handle_mob_death(attacker.game, target, attacker)
        elif isinstance(target, Player):
            combat_processor.handle_player_death(attacker.game, target, attacker)
        return
        
    # Trigger Combat State
    if not attacker.fighting and target.hp > 0:
        attacker.fighting = target
        attacker.state = "combat"
        attacker.send_line(f"{Colors.RED}You attack {target.name}!{Colors.RESET}")
        
    if hasattr(target, 'fighting'):
        if not target.fighting:
            target.fighting = attacker
            if hasattr(target, 'state'): target.state = "combat"
        if attacker not in target.attackers:
            target.attackers.append(attacker)


# --- Skill Handlers ---
# Return format: (target_entity, stop_execution)

def handle_buff(player, skill, args):
    """Handles self-buffs like Rage or Stone Skin."""
    if "rage" in skill.identity_tags:
        status_effects_engine.apply_effect(player, "berserk_rage", 20)
        player.send_line(f"{Colors.RED}You roar with primal fury!{Colors.RESET}")
        player.room.broadcast(f"{player.name} roars with primal fury!", exclude_player=player)
    elif "stone_skin" in skill.identity_tags:
        status_effects_engine.apply_effect(player, "stone_skin", 60)
        player.send_line(f"{Colors.GREEN}Your skin hardens into impenetrable rock!{Colors.RESET}")
        player.room.broadcast(f"{player.name}'s skin turns grey and stony.", exclude_player=player)
    elif "crane_stance" in skill.identity_tags:
        status_effects_engine.apply_effect(player, "crane_stance", 60)
        player.send_line(f"{Colors.CYAN}You shift into the Crane Stance.{Colors.RESET}")
        player.room.broadcast(f"{player.name} assumes a graceful, defensive posture.", exclude_player=player)
    elif "defensive_stance" in skill.identity_tags:
        status_effects_engine.apply_effect(player, "defensive_stance", 60)
        player.send_line(f"{Colors.YELLOW}You raise your guard, entering a Defensive Stance.{Colors.RESET}")
        player.room.broadcast(f"{player.name} adopts a guarded combat posture.", exclude_player=player)
    elif "venom_coat" in skill.identity_tags:
        status_effects_engine.apply_effect(player, "venom_coat", 60)
        player.send_line(f"{Colors.GREEN}You coat your weapon in vile toxins.{Colors.RESET}")
        player.room.broadcast(f"{player.name} coats their weapon in poison.", exclude_player=player)
    
    # Buffs consume resources immediately upon application
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)
    magic_engine.consume_pacing(player, skill)
    return None, True

def handle_alchemy(player, skill, args):
    direction = args.lower()
    if direction in player.room.exits:
        target_room = player.room.exits[direction]
        player.send_line(f"You hurl {skill.name} to the {direction}!")
        player.room.broadcast(f"{player.name} hurls a flask to the {direction}!", exclude_player=player)
    elif not direction:
        player.send_line(f"You smash {skill.name} on the ground!")
        player.room.broadcast(f"{player.name} smashes a flask on the ground!", exclude_player=player)
        target_room = player.room
    else:
        player.send_line("Invalid direction.")
        return None, True

    # Apply AoE Damage immediately
    power = blessings_engine.MathBridge.calculate_power(skill, player)
    targets = target_room.monsters + [p for p in target_room.players if p != player]
    
    if not targets:
        player.send_line("The flask explodes harmlessly.")
        if target_room != player.room:
            target_room.broadcast(f"A flask flies in and explodes!")
    else:
        for t in targets:
            _apply_damage(player, t, power, skill.name)
            if target_room != player.room:
                if hasattr(t, 'send_line'):
                    t.send_line(f"{Colors.RED}A flask flies in from nowhere! You take {power} damage!{Colors.RESET}")
        
        if target_room != player.room:
            target_room.broadcast(f"A flask thrown by {player.name} explodes!", exclude_player=player)

    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)
    magic_engine.consume_pacing(player, skill)
    return None, True

def handle_marksmanship(player, skill, args):
    if not player.locked_target:
        player.send_line("You have no target locked. Use 'aim' first.")
        return None, True
    
    t = player.locked_target
    if t.hp <= 0:
        player.send_line("Your target is already dead.")
        player.locked_target = None
        return None, True
        
    max_range = 10 if "farsight" in player.identity_tags else 5
    found_target, dist, _ = search.find_nearby(player.room, t.name, max_range=max_range)
    
    if not found_target or found_target != t:
        player.send_line("Your target is too far away to see.")
        player.locked_target = None
        return None, True
        
    player.send_line(f"You fire at {t.name}!")
    return t, False

def handle_necromancy(player, skill, args):
    corpse = next((i for i in player.room.items if isinstance(i, Corpse)), None)
    if not corpse:
        player.send_line("There are no corpses here to raise.")
        return None, True

    player.room.items.remove(corpse)
    player.room.broadcast(f"{player.name} chants over {corpse.name}, and it begins to twitch!", exclude_player=player)
    player.send_line(f"You breathe unlife into {corpse.name}!")
    mob_manager.spawn_mob(player.game, "skeleton", player.room)
    return None, True

def handle_beast_master(player, skill, args):
    pet = next((m for m in player.room.monsters if m.leader == player), None)
    if not pet:
        player.send_line("You have no companion to command.")
        return None, True

    player.send_line(f"You command {pet.name} to howl!")
    player.room.broadcast(f"{pet.name} lets out a piercing howl!", exclude_player=player)
    
    if len(player.room.monsters) < 6:
        mob_manager.spawn_mob(player.game, pet.prototype_id, player.room)
        player.room.broadcast(f"A new {pet.name} emerges from the wilds!")
    else:
        player.send_line("The area is too crowded.")
    return None, True

def handle_scout(player, skill, args):
    if not args:
        player.send_line("Track whom?")
        return None, True
    
    target, dist, direction = search.find_nearby(player.room, args, max_range=50)
    if not target:
        player.send_line("You cannot find any sign of them.")
        return None, True
        
    is_stealthed = "stealth" in getattr(target, 'tags', []) or "stealth" in getattr(target, 'identity_tags', [])
    if is_stealthed and "eagle_eye" not in player.identity_tags:
        player.send_line("You cannot find any sign of them.")
    else:
        player.send_line(f"You find tracks leading {Colors.CYAN}{direction}{Colors.RESET}.")
    return None, True

def handle_thievery(player, skill, args):
    target = find_by_index(player.room.monsters + player.room.players, args)
    if not target:
        player.send_line("Steal from whom?")
        return None, True

    if target == player:
        player.send_line("You cannot steal from yourself.")
        return None, True

    # Success Check: (Dex + Luk) vs (Target Wis + Level)
    thief_score = player.get_stat('dex') + player.get_stat('luk') + random.randint(1, 20)
    # Simple target score approximation
    target_wis = getattr(target, 'base_stats', {}).get('wis', 10) if hasattr(target, 'base_stats') else 10
    target_score = target_wis + 10 + random.randint(1, 20)

    if thief_score < target_score:
        player.send_line(f"{Colors.RED}You are caught trying to steal from {target.name}!{Colors.RESET}")
        target.send_line(f"{Colors.RED}{player.name} tried to steal from you!{Colors.RESET}")
        # Trigger combat if caught
        return target, False

    # Success!
    if "mug" in skill.identity_tags:
        # Mug deals damage AND steals gold
        gold_stolen = random.randint(1, 10)
        target.gold = max(0, target.gold - gold_stolen)
        player.gold += gold_stolen
        player.send_line(f"You mug {target.name} for {gold_stolen} gold!")
        return target, False # Return target so damage is applied by _execute_skill
    else:
        # Steal just takes gold/items without combat (if successful)
        gold_stolen = random.randint(1, 5)
        if target.gold > 0:
            actual_stolen = min(target.gold, gold_stolen)
            target.gold -= actual_stolen
            player.gold += actual_stolen
            player.send_line(f"You deftly swipe {actual_stolen} gold from {target.name}.")
        else:
            player.send_line(f"{target.name} has no gold.")
        return None, True

def handle_temporal(player, skill, args):
    if "phase_bubble" in skill.identity_tags:
        # Apply a status effect that allows passing locked doors (logic to be added in movement)
        status_effects_engine.apply_effect(player, "phased", 30)
        player.send_line(f"{Colors.CYAN}You shift slightly out of phase with reality.{Colors.RESET}")
        player.room.broadcast(f"{player.name} begins to shimmer and turn translucent.", exclude_player=player)
        return None, True
    
    return None, True

def handle_shield_bash(player, skill, args):
    # Target required
    target = find_by_index(player.room.monsters + player.room.players, args)
    if not target and player.fighting:
        target = player.fighting
        
    if not target:
        player.send_line("Shield bash whom?")
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
        status_effects_engine.apply_effect(target, "stun", 4)
        player.send_line(f"{Colors.YELLOW}You smash the pommel into {target.name}'s face!{Colors.RESET}")
    return target, False

def handle_trip(player, skill, args):
    target = find_by_index(player.room.monsters + player.room.players, args) if args else player.fighting
    if target:
        status_effects_engine.apply_effect(target, "stun", 4)
        player.send_line(f"{Colors.YELLOW}You sweep {target.name}'s legs, knocking them down!{Colors.RESET}")
    return target, False

def handle_poison(player, skill, args):
    target = find_by_index(player.room.monsters + player.room.players, args) if args else player.fighting
    if target:
        status_effects_engine.apply_effect(target, "poison", 20)
        player.send_line(f"{Colors.GREEN}You infect {target.name} with poison!{Colors.RESET}")
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

def handle_scare(player, skill, args):
    target = find_by_index(player.room.monsters + player.room.players, args) if args else player.fighting
    if target:
        status_effects_engine.apply_effect(target, "fear", 10)
        player.send_line(f"{Colors.RED}You scream at {target.name}, filling them with fear!{Colors.RESET}")
        # Force flee logic could go here or be handled by the fear effect in combat_processor
        if hasattr(target, 'send_line'):
            target.send_line(f"{Colors.RED}You are terrified of {player.name}!{Colors.RESET}")
    return target, False

def handle_struggle(player, skill, args):
    # Removes net/web
    removed = []
    if player.status_effects:
        for eff in ["net", "web", "root", "grapple"]:
            if eff in player.status_effects:
                status_effects_engine.remove_effect(player, eff)
                removed.append(eff)
    
    if removed:
        player.send_line(f"You struggle and break free from: {', '.join(removed)}!")
    else:
        player.send_line("You struggle, but you aren't restrained.")
    return None, True

def handle_backstab(player, skill, args):
    target = find_by_index(player.room.monsters + player.room.players, args) if args else player.fighting
    if not target:
        player.send_line("Backstab whom?")
        return None, True

    # Requirement: Player not fighting target directly
    if player.fighting == target:
        player.send_line("You cannot backstab a target that is focused on you!")
        return None, True
        
    # Requirement: Target is fighting someone else (distracted)
    if not target.fighting:
        player.send_line("The target is wary. Wait for them to be distracted.")
        return None, True

    # Calculate Power
    power = blessings_engine.MathBridge.calculate_power(skill, player)
    
    # Weapon Check for multiplier
    multiplier = 1.5
    if player.equipped_weapon and any(w in player.equipped_weapon.name.lower() for w in ["dagger", "knife", "blade"]):
        multiplier = 5.0
    
    final_power = int(power * multiplier)
    
    player.send_line(f"{Colors.RED}BACKSTAB!{Colors.RESET}")
    _apply_damage(player, target, final_power, skill.name)

    # Consume resources here since we are stopping execution
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)
    magic_engine.consume_pacing(player, skill)

    return None, True
import random
from logic.engines import blessings_engine, magic_engine, status_effects_engine, combat_processor
from logic import mob_manager, search
from utilities.colors import Colors
from utilities import combat_formatter
from logic.common import find_by_index, get_reverse_direction
from models import Corpse, Monster, Player

# --- Private Helpers ---

def _apply_damage(attacker, target, damage, source_name):
    # Apply Defense
    defense = 0
    if hasattr(target, 'get_defense'):
        defense = target.get_defense()
    elif hasattr(target, 'equipped_armor') and target.equipped_armor:
        defense = target.equipped_armor.defense
    
    # Apply Body Part Multipliers (e.g. Broken Shell)
    multiplier = 1.0
    if hasattr(target, 'get_damage_modifier'):
        multiplier = target.get_damage_modifier()

    final_damage = max(1, int((damage - defense) * multiplier))
    target.hp -= final_damage
    
    # Messaging
    att_msg, tgt_msg, _ = combat_formatter.format_damage(attacker.name, target.name, final_damage, source=source_name)
    attacker.send_line(att_msg)
    if hasattr(target, 'send_line'):
        target.send_line(tgt_msg)
        
    # Death Check (Simplified, relies on next heartbeat to clean up corpse usually, 
    # but we can trigger death logic here if we want instant feedback)
    if target.hp <= 0:
        attacker.send_line(f"{Colors.BOLD}{Colors.YELLOW}You have defeated {target.name}!{Colors.RESET}")
        # Execute death logic immediately
        if isinstance(target, Monster):
            combat_processor.handle_mob_death(attacker.game, target, attacker)
        elif isinstance(target, Player):
            combat_processor.handle_player_death(attacker.game, target, attacker)
        return
        
    # Trigger Combat State
    if not attacker.fighting and target.hp > 0:
        attacker.fighting = target
        attacker.state = "combat"
        attacker.send_line(f"{Colors.RED}You attack {target.name}!{Colors.RESET}")
        
    if hasattr(target, 'fighting'):
        if not target.fighting:
            target.fighting = attacker
            if hasattr(target, 'state'): target.state = "combat"
        if attacker not in target.attackers:
            target.attackers.append(attacker)


# --- Skill Handlers ---
# Return format: (target_entity, stop_execution)

def handle_buff(player, skill, args):
    """Handles self-buffs like Rage or Stone Skin."""
    if "rage" in skill.identity_tags:
        status_effects_engine.apply_effect(player, "berserk_rage", 20)
        player.send_line(f"{Colors.RED}You roar with primal fury!{Colors.RESET}")
        player.room.broadcast(f"{player.name} roars with primal fury!", exclude_player=player)
    elif "stone_skin" in skill.identity_tags:
        status_effects_engine.apply_effect(player, "stone_skin", 60)
        player.send_line(f"{Colors.GREEN}Your skin hardens into impenetrable rock!{Colors.RESET}")
        player.room.broadcast(f"{player.name}'s skin turns grey and stony.", exclude_player=player)
    elif "crane_stance" in skill.identity_tags:
        status_effects_engine.apply_effect(player, "crane_stance", 60)
        player.send_line(f"{Colors.CYAN}You shift into the Crane Stance.{Colors.RESET}")
        player.room.broadcast(f"{player.name} assumes a graceful, defensive posture.", exclude_player=player)
    elif "defensive_stance" in skill.identity_tags:
        status_effects_engine.apply_effect(player, "defensive_stance", 60)
        player.send_line(f"{Colors.YELLOW}You raise your guard, entering a Defensive Stance.{Colors.RESET}")
        player.room.broadcast(f"{player.name} adopts a guarded combat posture.", exclude_player=player)
    elif "venom_coat" in skill.identity_tags:
        status_effects_engine.apply_effect(player, "venom_coat", 60)
        player.send_line(f"{Colors.GREEN}You coat your weapon in vile toxins.{Colors.RESET}")
        player.room.broadcast(f"{player.name} coats their weapon in poison.", exclude_player=player)
    
    # Buffs consume resources immediately upon application
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)
    magic_engine.consume_pacing(player, skill)
    return None, True

def handle_alchemy(player, skill, args):
    direction = args.lower()
    if direction in player.room.exits:
        target_room = player.room.exits[direction]
        player.send_line(f"You hurl {skill.name} to the {direction}!")
        player.room.broadcast(f"{player.name} hurls a flask to the {direction}!", exclude_player=player)
    elif not direction:
        player.send_line(f"You smash {skill.name} on the ground!")
        player.room.broadcast(f"{player.name} smashes a flask on the ground!", exclude_player=player)
        target_room = player.room
    else:
        player.send_line("Invalid direction.")
        return None, True

    # Apply AoE Damage immediately
    power = blessings_engine.MathBridge.calculate_power(skill, player)
    targets = target_room.monsters + [p for p in target_room.players if p != player]
    
    if not targets:
        player.send_line("The flask explodes harmlessly.")
        if target_room != player.room:
            target_room.broadcast(f"A flask flies in and explodes!")
    else:
        for t in targets:
            _apply_damage(player, t, power, skill.name)
            if target_room != player.room:
                if hasattr(t, 'send_line'):
                    t.send_line(f"{Colors.RED}A flask flies in from nowhere! You take {power} damage!{Colors.RESET}")
        
        if target_room != player.room:
            target_room.broadcast(f"A flask thrown by {player.name} explodes!", exclude_player=player)

    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)
    magic_engine.consume_pacing(player, skill)
    return None, True

def handle_marksmanship(player, skill, args):
    if not player.locked_target:
        player.send_line("You have no target locked. Use 'aim' first.")
        return None, True
    
    t = player.locked_target
    if t.hp <= 0:
        player.send_line("Your target is already dead.")
        player.locked_target = None
        return None, True
        
    max_range = 10 if "farsight" in player.identity_tags else 5
    found_target, dist, _ = search.find_nearby(player.room, t.name, max_range=max_range)
    
    if not found_target or found_target != t:
        player.send_line("Your target is too far away to see.")
        player.locked_target = None
        return None, True
        
    player.send_line(f"You fire at {t.name}!")
    return t, False

def handle_necromancy(player, skill, args):
    corpse = next((i for i in player.room.items if isinstance(i, Corpse)), None)
    if not corpse:
        player.send_line("There are no corpses here to raise.")
        return None, True

    player.room.items.remove(corpse)
    player.room.broadcast(f"{player.name} chants over {corpse.name}, and it begins to twitch!", exclude_player=player)
    player.send_line(f"You breathe unlife into {corpse.name}!")
    mob_manager.spawn_mob(player.game, "skeleton", player.room)
    return None, True

def handle_beast_master(player, skill, args):
    pet = next((m for m in player.room.monsters if m.leader == player), None)
    if not pet:
        player.send_line("You have no companion to command.")
        return None, True

    player.send_line(f"You command {pet.name} to howl!")
    player.room.broadcast(f"{pet.name} lets out a piercing howl!", exclude_player=player)
    
    if len(player.room.monsters) < 6:
        mob_manager.spawn_mob(player.game, pet.prototype_id, player.room)
        player.room.broadcast(f"A new {pet.name} emerges from the wilds!")
    else:
        player.send_line("The area is too crowded.")
    return None, True

def handle_scout(player, skill, args):
    if not args:
        player.send_line("Track whom?")
        return None, True
    
    target, dist, direction = search.find_nearby(player.room, args, max_range=50)
    if not target:
        player.send_line("You cannot find any sign of them.")
        return None, True
        
    is_stealthed = "stealth" in getattr(target, 'tags', []) or "stealth" in getattr(target, 'identity_tags', [])
    if is_stealthed and "eagle_eye" not in player.identity_tags:
        player.send_line("You cannot find any sign of them.")
    else:
        player.send_line(f"You find tracks leading {Colors.CYAN}{direction}{Colors.RESET}.")
    return None, True

def handle_thievery(player, skill, args):
    target = find_by_index(player.room.monsters + player.room.players, args)
    if not target:
        player.send_line("Steal from whom?")
        return None, True

    if target == player:
        player.send_line("You cannot steal from yourself.")
        return None, True

    # Success Check: (Dex + Luk) vs (Target Wis + Level)
    thief_score = player.get_stat('dex') + player.get_stat('luk') + random.randint(1, 20)
    # Simple target score approximation
    target_wis = getattr(target, 'base_stats', {}).get('wis', 10) if hasattr(target, 'base_stats') else 10
    target_score = target_wis + 10 + random.randint(1, 20)

    if thief_score < target_score:
        player.send_line(f"{Colors.RED}You are caught trying to steal from {target.name}!{Colors.RESET}")
        target.send_line(f"{Colors.RED}{player.name} tried to steal from you!{Colors.RESET}")
        # Trigger combat if caught
        return target, False

    # Success!
    if "mug" in skill.identity_tags:
        # Mug deals damage AND steals gold
        gold_stolen = random.randint(1, 10)
        target.gold = max(0, target.gold - gold_stolen)
        player.gold += gold_stolen
        player.send_line(f"You mug {target.name} for {gold_stolen} gold!")
        return target, False # Return target so damage is applied by _execute_skill
    else:
        # Steal just takes gold/items without combat (if successful)
        gold_stolen = random.randint(1, 5)
        if target.gold > 0:
            actual_stolen = min(target.gold, gold_stolen)
            target.gold -= actual_stolen
            player.gold += actual_stolen
            player.send_line(f"You deftly swipe {actual_stolen} gold from {target.name}.")
        else:
            player.send_line(f"{target.name} has no gold.")
        return None, True

def handle_temporal(player, skill, args):
    if "phase_bubble" in skill.identity_tags:
        # Apply a status effect that allows passing locked doors (logic to be added in movement)
        status_effects_engine.apply_effect(player, "phased", 30)
        player.send_line(f"{Colors.CYAN}You shift slightly out of phase with reality.{Colors.RESET}")
        player.room.broadcast(f"{player.name} begins to shimmer and turn translucent.", exclude_player=player)
        return None, True
    
    return None, True

def handle_shield_bash(player, skill, args):
    # Target required
    target = find_by_index(player.room.monsters + player.room.players, args)
    if not target and player.fighting:
        target = player.fighting
        
    if not target:
        player.send_line("Shield bash whom?")
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
        status_effects_engine.apply_effect(target, "stun", 4)
        player.send_line(f"{Colors.YELLOW}You smash the pommel into {target.name}'s face!{Colors.RESET}")
    return target, False

def handle_trip(player, skill, args):
    target = find_by_index(player.room.monsters + player.room.players, args) if args else player.fighting
    if target:
        status_effects_engine.apply_effect(target, "stun", 4)
        player.send_line(f"{Colors.YELLOW}You sweep {target.name}'s legs, knocking them down!{Colors.RESET}")
    return target, False

def handle_poison(player, skill, args):
    target = find_by_index(player.room.monsters + player.room.players, args) if args else player.fighting
    if target:
        status_effects_engine.apply_effect(target, "poison", 20)
        player.send_line(f"{Colors.GREEN}You infect {target.name} with poison!{Colors.RESET}")
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

def handle_scare(player, skill, args):
    target = find_by_index(player.room.monsters + player.room.players, args) if args else player.fighting
    if target:
        status_effects_engine.apply_effect(target, "fear", 10)
        player.send_line(f"{Colors.RED}You scream at {target.name}, filling them with fear!{Colors.RESET}")
        # Force flee logic could go here or be handled by the fear effect in combat_processor
        if hasattr(target, 'send_line'):
            target.send_line(f"{Colors.RED}You are terrified of {player.name}!{Colors.RESET}")
    return target, False

def handle_struggle(player, skill, args):
    # Removes net/web
    removed = []
    if player.status_effects:
        for eff in ["net", "web", "root", "grapple"]:
            if eff in player.status_effects:
                status_effects_engine.remove_effect(player, eff)
                removed.append(eff)
    
    if removed:
        player.send_line(f"You struggle and break free from: {', '.join(removed)}!")
    else:
        player.send_line("You struggle, but you aren't restrained.")
    return None, True

def handle_backstab(player, skill, args):
    target = find_by_index(player.room.monsters + player.room.players, args) if args else player.fighting
    if not target:
        player.send_line("Backstab whom?")
        return None, True

    # Requirement: Player not fighting target directly
    if player.fighting == target:
        player.send_line("You cannot backstab a target that is focused on you!")
        return None, True
        
    # Requirement: Target is fighting someone else (distracted)
    if not target.fighting:
        player.send_line("The target is wary. Wait for them to be distracted.")
        return None, True

    # Calculate Power
    power = blessings_engine.MathBridge.calculate_power(skill, player)
    
    # Weapon Check for multiplier
    multiplier = 1.5
    if player.equipped_weapon and any(w in player.equipped_weapon.name.lower() for w in ["dagger", "knife", "blade"]):
        multiplier = 5.0
    
    final_power = int(power * multiplier)
    
    player.send_line(f"{Colors.RED}BACKSTAB!{Colors.RESET}")
    _apply_damage(player, target, final_power, skill.name)

    # Consume resources here since we are stopping execution
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)
    magic_engine.consume_pacing(player, skill)

    return None, True