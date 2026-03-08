import random
import asyncio
import logging
from models import Monster, Player
from logic.engines import combat_engine
from logic.core import event_engine
from utilities.colors import Colors
from logic.engines import vision_engine
from logic.engines import combat_actions
from logic.engines import combat_ai
from logic.engines import combat_lifecycle
from utilities import telemetry

# Initialize Passives (Register Listeners)
import logic.passives

logger = logging.getLogger("GodlessMUD")

# Track rooms with active combat to ensure they spin down correctly when players leave
_ACTIVE_COMBAT_ROOM_IDS = set()

def process_round(game):
    global _ACTIVE_COMBAT_ROOM_IDS
    """
    Main combat loop processor.
    Iterates through all rooms and handles combat rounds for players and mobs.
    """
    # logger.debug("process_round executing")
    
    # Optimization: Only check rooms with players or active combat
    rooms_to_process = {p.room for p in game.players.values() if p.room}
    for room_id in _ACTIVE_COMBAT_ROOM_IDS:
        room = game.world.rooms.get(room_id)
        if room:
            rooms_to_process.add(room)
            
    # logger.debug(f"Checking {len(rooms_to_process)} active rooms for combat.")
    next_active_ids = set()

    # Optimization: Cache visibility results for this tick to prevent redundant raycasts
    visibility_cache = {}

    for room in rooms_to_process:
        # Start buffering for all players in the room to ensure atomic packet delivery
        for p in room.players:
            p.start_buffering()
            
        # 0. Check for Aggro (Initiate Combat)
        combat_ai.check_aggro(room)

        players_to_prompt = set()
        
        # Collect all active fighters
        combatants = [p for p in room.players if p.fighting] + [m for m in room.monsters if m.fighting]
        
        if combatants:
            logger.debug(f"[COMBAT] Room {room.id}: Processing {len(combatants)} fighters.")
            
        for combatant in combatants:
            _process_turn(combatant, room, game, players_to_prompt, visibility_cache)

        # Send prompts once per tick
        # [PATCH] Filter out players involved in death events (handled by Reaper to ensure message ordering)
        deferred_players = set()
        if hasattr(game, 'dead_entities'):
            for d in game.dead_entities:
                if isinstance(d.get('killer'), Player):
                    deferred_players.add(d['killer'])
                if isinstance(d.get('victim'), Player):
                    deferred_players.add(d['victim'])

        for p in players_to_prompt:
            if p not in deferred_players:
                p.send_line(p.get_prompt())
            
        # Track active combat for next tick
        has_combat = False
        if any(p.fighting for p in room.players):
            has_combat = True
        elif any(m.fighting for m in room.monsters):
            has_combat = True
            
        if has_combat:
            next_active_ids.add(room.id)

        # Flush buffers for all players in the room
        for p in room.players:
            p.stop_buffering()
            # [PATCH] Force push packets to client immediately (Fixes laggy output)
            if hasattr(p, 'drain'):
                asyncio.create_task(p.drain())

    _ACTIVE_COMBAT_ROOM_IDS = next_active_ids
    # logger.debug("process_round complete")
    
    # [REAPER] Process deferred deaths safely outside the iteration loop
    combat_lifecycle.process_dead_queue(game)

def _process_turn(combatant, room, game, players_to_prompt, visibility_cache=None):
    """
    Unified turn processor for both Players and Monsters.
    """
    if combatant.hp <= 0:
        return

    target = combatant.fighting
    
    # 1. Event: Turn Start
    turn_ctx = {
        'entity': combatant, 
        'game': game, 
        'target': target,
        'action_taken': False
    }
    event_engine.dispatch("combat_turn_start", turn_ctx)
    
    if turn_ctx['action_taken']:
        return # AI or something else handled the turn

    # 2. Mob Specific AI/Behavior (Pre-Validation)
    combat_ai.update_mob_tactics(combatant)

    # 3. Validation & Targeting
    target = combatant.fighting # Re-fetch in case changed
    
    is_valid = combat_engine.validate_target(combatant, target)
    target_is_dead = target and target.hp <= 0
    
    # Visibility Check with Caching
    can_see_target = False
    if target:
        if visibility_cache is not None:
            cache_key = (combatant, target)
            if cache_key not in visibility_cache:
                visibility_cache[cache_key] = vision_engine.can_see(combatant, target)
            can_see_target = visibility_cache[cache_key]
        else:
            can_see_target = vision_engine.can_see(combatant, target)
    
    if not is_valid or target_is_dead or not can_see_target:
        if isinstance(combatant, Player):
            # [PATCH] If target is dead and pending cleanup, do not drop combat yet.
            # This prevents "You are no longer fighting" from appearing between the kill and the reaper cleanup.
            if target_is_dead and getattr(target, 'pending_death', False):
                return

            # Player Auto-Switch
            logger.debug(f"[COMBAT_TRACE] Auto-switch for {combatant.name}. Target dead/invalid. Checking {len(combatant.attackers)} attackers.")
            valid_attackers = []
            for a in combatant.attackers:
                is_val = combat_engine.validate_target(combatant, a)
                logger.debug(f"[COMBAT_TRACE] Checking attacker {a.name} (HP: {a.hp}): Valid={is_val}")
                if is_val:
                    valid_attackers.append(a)
            combatant.attackers = valid_attackers
            
            if valid_attackers:
                new_target = valid_attackers[0]
                combatant.fighting = new_target
                combatant.send_line(f"You turn to fight {new_target.name}!")
                target = new_target
                # Assume valid for this turn to prevent skipping
                is_valid = True
                
                # Update cache for new target
                if visibility_cache is not None:
                    cache_key = (combatant, target)
                    if cache_key not in visibility_cache:
                        visibility_cache[cache_key] = vision_engine.can_see(combatant, target)
                    can_see_target = visibility_cache[cache_key]
                else:
                    can_see_target = vision_engine.can_see(combatant, target)
            else:
                if target and not target_is_dead and can_see_target:
                     logger.warning(f"Dropping combat for {combatant.name}. Target {target.name} invalid.")
                combatant.send_line(f"You are no longer fighting.")
                combatant.fighting = None
                combatant.state = "normal"
                players_to_prompt.add(combatant)
                return
        else:
            # Mob Logic
            target_dead_pending = target and target.hp <= 0 and (target in room.monsters or target in room.players)
            if (not is_valid or not can_see_target) and not target_dead_pending:
                combatant.fighting = None
                return
            if target_dead_pending:
                 pass # Continue to process death logic if needed
            else:
                 return

    # 4. Execute Attack
    if target and target.hp > 0:
        # Skip attack if incapacitated or busy
        is_stunned = "stun" in getattr(combatant, 'status_effects', {})
        state = getattr(combatant, 'state', 'normal')
        if is_stunned or state in ["stunned", "casting", "resting"]:
            return
            
        # Mob Skill Logic
        skill_to_use = combat_ai.select_mob_skill(combatant, game)
            
        combat_actions.execute_attack(combatant, target, room, game, players_to_prompt, blessing=skill_to_use)
        
        # 5. Event: Turn End (Post-Attack)
        end_ctx = {'entity': combatant, 'target': target, 'game': game}
        event_engine.dispatch("combat_turn_end", end_ctx)

def handle_mob_death(game, mob, killer):
    """Legacy wrapper for backward compatibility with skill_utils."""
    combat_lifecycle.handle_death(game, mob, killer)

def handle_player_death(game, player, killer):
    """Legacy wrapper for backward compatibility."""
    combat_lifecycle.handle_death(game, player, killer)

def execute_attack(combatant, target, room, game, players_to_prompt, blessing=None):
    """Legacy wrapper for backward compatibility with base_executor."""
    combat_actions.execute_attack(combatant, target, room, game, players_to_prompt, blessing)