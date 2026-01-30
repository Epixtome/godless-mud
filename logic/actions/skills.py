import logic.command_manager as command_manager
from logic.engines import blessings_engine
from logic.engines import combat_engine
from logic.engines import magic_engine
from logic.engines import combat_processor
from logic.engines import status_effects_engine
from logic import mob_manager
from logic import search
from utilities.colors import Colors
from utilities import combat_formatter
from logic.common import find_by_index
from models import Corpse

def try_execute_skill(player, command_line):
    """
    Parses input to see if it matches an equipped skill (blessing).
    Syntax: <skill_name> [target/direction]
    Example: "kick goblin", "flask_toss north", "snipe"
    """
    parts = command_line.split()
    trigger = parts[0].lower()
    args = " ".join(parts[1:]) if len(parts) > 1 else ""
    
    # Find blessing by name in equipped list
    # Support fuzzy matching (e.g. "charge" -> "mounted_charge")
    skill = None
    candidates = []
    for b_id in player.equipped_blessings:
        b = player.game.world.blessings.get(b_id)
        if b:
            # Ensure it is actually a skill (not a spell like Farsight)
            if "skill" not in b.identity_tags:
                continue

            b_name = b.name.lower().replace(" ", "_")
            if b_name == trigger:
                skill = b
                break
            elif trigger in b_name:
                candidates.append(b)
    
    if not skill and len(candidates) == 1:
        skill = candidates[0]
            
    if not skill:
        return False

    # It's a skill! Execute it.
    _execute_skill(player, skill, args)
    return True

def _execute_skill(player, skill, args):
    # 1. Validation (Auditor)
    can_cast, reason = blessings_engine.Auditor.can_invoke(skill, player)
    if not can_cast:
        player.send_line(reason)
        return

    # 1.5 Pacing Check (Actions per Round)
    can_pace, reason_pace = magic_engine.check_pacing(player, skill)
    if not can_pace:
        player.send_line(reason_pace)
        return

    # 1.8 Buffs / Status Effects (Self-Cast)
    # Handles skills that apply a state to the user without needing a target (e.g., Rage)
    if "buff" in skill.identity_tags:
        if "rage" in skill.identity_tags:
            status_effects_engine.apply_effect(player, "berserk_rage", 20) # 20 seconds
            player.send_line(f"{Colors.RED}You roar with primal fury!{Colors.RESET}")
            player.room.broadcast(f"{player.name} roars with primal fury!", exclude_player=player)
            magic_engine.consume_resources(player, skill)
            magic_engine.set_cooldown(player, skill)
            magic_engine.consume_pacing(player, skill)
            return
        elif "stone_skin" in skill.identity_tags:
            status_effects_engine.apply_effect(player, "stone_skin", 60) # 60 seconds
            player.send_line(f"{Colors.GREEN}Your skin hardens into impenetrable rock!{Colors.RESET}")
            player.room.broadcast(f"{player.name}'s skin turns grey and stony.", exclude_player=player)
            magic_engine.consume_resources(player, skill)
            magic_engine.set_cooldown(player, skill)
            magic_engine.consume_pacing(player, skill)
            return
        elif "crane_stance" in skill.identity_tags:
            status_effects_engine.apply_effect(player, "crane_stance", 60)
            player.send_line(f"{Colors.CYAN}You shift into the Crane Stance.{Colors.RESET}")
            player.room.broadcast(f"{player.name} assumes a graceful, defensive posture.", exclude_player=player)
            magic_engine.consume_resources(player, skill)
            magic_engine.set_cooldown(player, skill)
            magic_engine.consume_pacing(player, skill)
            return

    # 2. Targeting Logic
    target = None
    target_room = player.room
    
    # A. Directional AoE (Alchemist)
    if "alchemy" in skill.identity_tags and "ranged" in skill.identity_tags:
        direction = args.lower()
        if direction in player.room.exits:
            target_room = player.room.exits[direction]
            player.send_line(f"You hurl {skill.name} to the {direction}!")
            player.room.broadcast(f"{player.name} hurls a flask to the {direction}!", exclude_player=player)
        elif not direction:
            # Target current room
            player.send_line(f"You smash {skill.name} on the ground!")
            player.room.broadcast(f"{player.name} smashes a flask on the ground!", exclude_player=player)
        else:
            player.send_line("Invalid direction.")
            return
            
    # B. Ranged Locking (Ranger)
    elif "marksmanship" in skill.identity_tags:
        if not player.locked_target:
            player.send_line("You have no target locked. Use 'aim' first.")
            return
        
        # Verify target is still valid/alive
        t = player.locked_target
        if t.hp <= 0:
            player.send_line("Your target is already dead.")
            player.locked_target = None
            return
            
        # Verify range
        max_range = 5 # Standard snipe range
        if "farsight" in player.identity_tags:
            max_range = 10
            
        found_target, dist, _ = search.find_nearby(player.room, t.name, max_range=max_range)
        if not found_target or found_target != t:
            player.send_line("Your target is too far away to see.")
            player.locked_target = None
            return
            
        target = t
        player.send_line(f"You fire at {target.name}!")

    # C. Necromancy (Raise Dead)
    elif "raise_dead" in skill.identity_tags:
        # Find a corpse
        corpse = None
        for item in player.room.items:
            if isinstance(item, Corpse):
                corpse = item
                break
        
        if not corpse:
            player.send_line("There are no corpses here to raise.")
            return

        # Consume corpse
        player.room.items.remove(corpse)
        player.room.broadcast(f"{player.name} chants over {corpse.name}, and it begins to twitch!", exclude_player=player)
        player.send_line(f"You breathe unlife into {corpse.name}!")

        # Spawn Minion (Generic Skeleton for now)
        mob_manager.spawn_mob(player.game, "skeleton", player.room)
        # Note: In a full implementation, we'd set the minion's leader to 'player' here.
        return

    # D. Beast Master (Howl)
    elif "howl" in skill.identity_tags:
        # Find pet
        pet = None
        for m in player.room.monsters:
            if m.leader == player:
                pet = m
                break
        
        if not pet:
            player.send_line("You have no companion to command.")
            return

        player.send_line(f"You command {pet.name} to howl!")
        player.room.broadcast(f"{pet.name} lets out a piercing howl!", exclude_player=player)
        
        # Trigger Rally (Spawn a copy of the pet)
        if len(player.room.monsters) < 6:
            mob_manager.spawn_mob(player.game, pet.prototype_id, player.room)
            player.room.broadcast(f"A new {pet.name} emerges from the wilds!")
        else:
            player.send_line("The area is too crowded.")
        return
        
    # F. Scout (Track)
    elif "track" in skill.identity_tags:
        if not args:
            player.send_line("Track whom?")
            return
            
        # Search wide range (e.g. 50 rooms)
        target, dist, direction = search.find_nearby(player.room, args, max_range=50)
        
        if not target:
            player.send_line("You cannot find any sign of them.")
            return
            
        # Stealth Check
        is_stealthed = "stealth" in getattr(target, 'tags', []) or "stealth" in getattr(target, 'identity_tags', [])
        has_eagle_eye = "eagle_eye" in player.identity_tags
        
        if is_stealthed and not has_eagle_eye:
            player.send_line("You cannot find any sign of them.")
        else:
            player.send_line(f"You find tracks leading {Colors.CYAN}{direction}{Colors.RESET}.")
        return

    # E. Warrior (Sunder)
    elif "sunder" in skill.identity_tags:
        if not args:
            player.send_line("Sunder what?")
            return
            
        parts = args.split()
        target_name = parts[0]
        part_name = parts[1] if len(parts) > 1 else None
        
        target = find_by_index(player.room.monsters + player.room.players, target_name)
        if not target:
            player.send_line("You don't see them here.")
            return
            
        if not hasattr(target, 'body_parts') or not target.body_parts:
            player.send_line(f"{target.name} has no weak points to sunder.")
            return
            
        if not part_name:
            player.send_line(f"Sunder which part? ({', '.join(target.body_parts.keys())})")
            return
            
        if part_name not in target.body_parts:
            player.send_line(f"{target.name} does not have a '{part_name}'.")
            return
            
        part = target.body_parts[part_name]
        if part.get('destroyed', False):
            player.send_line(f"The {part_name} is already broken!")
            return
            
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
            
        return

    # C. Standard Melee/Room
    else:
        if args:
            target = find_by_index(player.room.monsters + player.room.players, args)
            if not target:
                player.send_line("You don't see them here.")
                return
        elif player.fighting:
            target = player.fighting
        else:
            player.send_line("Use skill on whom?")
            return

    # 3. Apply Effects
    # Calculate Power
    power = blessings_engine.MathBridge.calculate_power(skill, player)
    
    # Handle AoE (Alchemist)
    if "alchemy" in skill.identity_tags:
        # Hit everything in target_room
        targets = target_room.monsters + [p for p in target_room.players if p != player]
        if not targets:
            player.send_line("The flask explodes harmlessly.")
            if target_room != player.room:
                target_room.broadcast(f"A flask flies in and explodes!")
            return
            
        for t in targets:
            _apply_damage(player, t, power, skill.name)
            if target_room != player.room:
                t.send_line(f"{Colors.RED}A flask flies in from nowhere! You take {power} damage!{Colors.RESET}")
        
        if target_room != player.room:
            target_room.broadcast(f"A flask thrown by {player.name} explodes!", exclude_player=player)
                
    # Handle Single Target
    elif target:
        # Prevent damage if it's a utility/buff skill that fell through
        if any(tag in skill.identity_tags for tag in ["buff", "utility", "passive", "protection", "aura"]):
            player.send_line(f"You use {skill.name}.")
        else:
            _apply_damage(player, target, power, skill.name)
        
    # 4. Consume Resources & Cooldown
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)
    magic_engine.consume_pacing(player, skill)
    
    # Chi Generation
    if "chi_builder" in skill.identity_tags:
        player.resources['chi'] = min(5, player.resources.get('chi', 0) + 1)
        player.send_line(f"{Colors.YELLOW}You gain 1 Chi.{Colors.RESET}")

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
        from models import Monster, Player
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