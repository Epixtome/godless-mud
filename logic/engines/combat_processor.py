import random
import logging
from models import Corpse, Monster, Player
from logic import mob_manager
from logic.engines import combat_engine
from logic.engines import status_effects_engine
from logic.engines import quest_engine
from utilities.colors import Colors
from utilities import combat_formatter

logger = logging.getLogger("GodlessMUD")

def process_round(game):
    """
    Main combat loop processor.
    Iterates through all rooms and handles combat rounds for players and mobs.
    """
    for room in game.world.rooms.values():
        # 0. Check for Aggro (Initiate Combat)
        _check_aggro(room)

        players_to_prompt = set()
        
        # --- Player Turns ---
        fighters = [p for p in room.players if p.fighting]
        
        for combatant in fighters:
            target = combatant.fighting
            
            # Validate Target
            is_valid = combat_engine.validate_target(combatant, target)
            target_dead_pending = target and target.hp <= 0 and (target in room.monsters or target in room.players)
            
            if not is_valid and not target_dead_pending:
                # Target invalid/dead/gone. Check for other attackers.
                valid_attackers = [a for a in combatant.attackers if combat_engine.validate_target(combatant, a)]
                combatant.attackers = valid_attackers
                
                if valid_attackers:
                    # Auto-switch to next attacker
                    new_target = valid_attackers[0]
                    combatant.fighting = new_target
                    combatant.send_line(f"You turn to fight {new_target.name}!")
                    target = new_target
                else:
                    if target:
                        logger.warning(f"Dropping combat for {combatant.name}. Target {target.name} invalid.")
                    combatant.send_line(f"You are no longer fighting.")
                    combatant.fighting = None
                    players_to_prompt.add(combatant)
                    continue

            # Calculate damage
            raw_damage = combat_engine.calculate_player_damage(combatant)
            
            # Apply Defense (Armor + Buffs)
            defense = 0
            if hasattr(target, 'get_defense'):
                defense = target.get_defense()
                
            # Apply Body Part Multipliers
            multiplier = 1.0
            if hasattr(target, 'get_damage_modifier'):
                multiplier = target.get_damage_modifier()

            damage = max(1, int((raw_damage - defense) * multiplier))
            target.hp -= damage
            
            if damage > 0:
                att_msg, tgt_msg, _ = combat_formatter.format_damage(combatant.name, target.name, damage)
                combatant.send_line(f"\r\n{att_msg}")
                
                # Weapon Effects (Bleed)
                if combatant.equipped_weapon and "bleed" in combatant.equipped_weapon.flags:
                    # Apply bleed for 10 seconds (5 ticks)
                    status_effects_engine.apply_effect(target, "bleed", 10)
                
            if hasattr(target, 'send_line'):
                target.send_line(f"\r\n{tgt_msg}")
                if hasattr(target, 'get_prompt'):
                    # Concentration Loss on Hit
                    conc_loss = random.randint(1, 5)
                    target.resources['concentration'] = max(0, target.resources.get('concentration', 0) - conc_loss)
                    players_to_prompt.add(target)
            
            if target.hp <= 0:
                combatant.send_line(f"{Colors.BOLD}{Colors.YELLOW}You have defeated {target.name}!{Colors.RESET}")
                target.fighting = None
                combatant.fighting = None
                combatant.state = "normal"
                
                if isinstance(target, Monster):
                    handle_mob_death(game, target, combatant)
                elif isinstance(target, Player):
                    handle_player_death(game, target, combatant)
            
            # Force prompt update every round
            players_to_prompt.add(combatant)

        # --- Monster Turns ---
        mob_fighters = [m for m in room.monsters if m.fighting]
        for mob in mob_fighters:
            target = mob.fighting
            
            # Companion Logic
            if mob.leader and mob.leader.room == mob.room:
                leader_target = mob.leader.fighting
                if leader_target and leader_target != mob and leader_target.hp > 0:
                    if not target or target.hp <= 0:
                        mob.fighting = leader_target
                        if mob not in leader_target.attackers:
                            leader_target.attackers.append(mob)
            
            # Auto-retaliate / Sticky Combat
            if target:
                if mob not in target.attackers:
                    target.attackers.append(mob)
                
                if not target.fighting or target.fighting.hp <= 0:
                    target.fighting = mob
                    target.state = "combat"

            # Rally Mechanic (Summon Help)
            if "rally" in mob.tags and mob.hp < mob.max_hp * 0.5:
                # 5% chance per round to rally if hurt
                if random.random() < 0.05:
                    # Limit number of mobs in room to prevent infinite spam
                    if len(room.monsters) < 6:
                        room.broadcast(f"{Colors.RED}{mob.name} howls for reinforcements!{Colors.RESET}")
                        # Spawn a copy of the same mob type
                        mob_manager.spawn_mob(game, mob.prototype_id, room)

            # Validate target
            is_valid = combat_engine.validate_target(mob, target)
            target_dead_pending = target and target.hp <= 0 and (target in room.monsters or target in room.players)
            
            if not is_valid and not target_dead_pending:
                mob.fighting = None
                continue
                
            # Calculate damage
            damage = combat_engine.calculate_mob_damage(mob, target)
            
            target.hp -= damage
            
            if damage > 0:
                _, tgt_msg, _ = combat_formatter.format_damage(mob.name, target.name, damage)
                if hasattr(target, 'send_line'):
                    target.send_line(f"\r\n{tgt_msg}")
            
            if target.hp <= 0:
                if hasattr(target, 'send_line'):
                    target.send_line(f"\n{Colors.BOLD}{Colors.RED}You have been defeated by {mob.name}!{Colors.RESET}")
                target.fighting = None
                mob.fighting = None
                
                if isinstance(target, Player):
                    handle_player_death(game, target, mob)
                elif isinstance(target, Monster):
                    handle_mob_death(game, target, mob)
            else:
                # Force prompt update for player being hit
                if isinstance(target, Player):
                    players_to_prompt.add(target)

        # Send prompts once per tick
        for p in players_to_prompt:
            p.send_line(p.get_prompt())

def _check_aggro(room):
    """
    Checks if any mobs in the room should initiate combat.
    Handles 'aggressive' and 'gatekeeper' tags.
    """
    if not room.players:
        return

    for mob in room.monsters:
        if mob.fighting:
            continue
            
        target = None
        
        # 1. Gatekeeper Logic (Attacks Criminals)
        if "gatekeeper" in mob.tags:
            for p in room.players:
                if p.reputation < -10: # Criminal Threshold
                    target = p
                    room.broadcast(f"{Colors.BOLD}{Colors.YELLOW}{mob.name} shouts: 'Halt, criminal!'{Colors.RESET}")
                    break
        
        # 2. Aggressive Logic (Attacks Random)
        elif "aggressive" in mob.tags:
            target = random.choice(room.players)
            
        if target and target.hp > 0:
            mob.fighting = target
            target.fighting = mob
            target.state = "combat"
            if mob not in target.attackers:
                target.attackers.append(mob)
            
            room.broadcast(f"{Colors.RED}{mob.name} attacks {target.name}!{Colors.RESET}")

def handle_mob_death(game, mob, killer):
    """Handles logic when a monster dies."""
    room = mob.room
    if not room:
        logger.error(f"Mob {mob.name} died but has no room reference.")
        return

    # Create corpse
    corpse = Corpse(f"corpse of {mob.name}", f"The dead body of {mob.name}.", mob.inventory)
    room.items.append(corpse)
    if mob in room.monsters:
        room.monsters.remove(mob)
    
    # Notify mob manager for respawn
    mob_manager.notify_death(game, mob)
    
    # Player specific rewards
    if isinstance(killer, Player):
        # Notify quest system
        if hasattr(killer, 'active_quests'):
            quest_engine.update_kill_progress(killer, mob.prototype_id)
            
        # Distribute Favor
        combat_engine.distribute_favor(killer, mob, game)

def handle_player_death(game, player, killer):
    """Handles logic when a player dies."""
    room = player.room
    
    # 1. Create Corpse with Gear
    corpse_inv = player.inventory[:]
    if player.equipped_armor:
        corpse_inv.append(player.equipped_armor)
        player.equipped_armor = None
    if player.equipped_weapon:
        corpse_inv.append(player.equipped_weapon)
        player.equipped_weapon = None
    
    player.inventory = [] # Strip player
    
    p_corpse = Corpse(f"corpse of {player.name}", f"The broken body of {player.name}.", corpse_inv)
    room.items.append(p_corpse)
    room.broadcast(f"{player.name} falls dead, dropping to the ground.", exclude_player=player)
    
    # 2. Resurrect at start room
    player.hp = player.max_hp
    player.resources['stamina'] = 10
    player.resources['concentration'] = 10
    player.is_resting = False
    player.state = "normal"
    player.fighting = None
    player.attackers = []
    
    # Determine Kingdom Respawn Point
    kingdom = player.identity_tags[0] if player.identity_tags else "neutral"
    target_id = getattr(game.world, 'landmarks', {}).get(f"{kingdom}_cap")
    
    start_room = game.world.rooms.get(target_id)
    if not start_room:
        start_room = game.world.start_room or list(game.world.rooms.values())[0]
    
    if player in room.players:
        room.players.remove(player)
    
    player.room = start_room
    start_room.players.append(player)
    
    player.send_line(f"\n{Colors.BOLD}{Colors.RED}You have died.{Colors.RESET}")
    player.send_line(f"{Colors.YELLOW}You wake up in {start_room.name}, naked and vulnerable.{Colors.RESET}")
    start_room.broadcast(f"{player.name} appears, looking dazed and recently deceased.", exclude_player=player)
    
    # Refresh view
    from logic.actions import information
    information.look(player, "")