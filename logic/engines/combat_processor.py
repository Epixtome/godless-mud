import random
import asyncio
import logging
from models import Monster, Player
from logic.core import combat
from logic.core import event_engine
from utilities.colors import Colors
from logic.engines import vision_engine
from logic.engines import combat_actions
from logic.core.systems import ai

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
        # 0. Check for Aggro (Initiate Combat via Event)
        event_engine.dispatch("room_combat_tick", room=room, game=game)

        # Mark that all players in combat rooms might need a prompt update
        for p in room.players:
            if p.fighting or p.attackers:
                p.prompt_requested = True

        players_to_prompt = set()
        
        # Collect all active fighters
        combatants = [p for p in room.players if p.fighting] + [m for m in room.monsters if m.fighting]
        
        if combatants:
            logger.debug(f"[COMBAT] Room {room.id}: Processing {len(combatants)} fighters.")
            
        for combatant in combatants:
            _process_turn(combatant, room, game, players_to_prompt, visibility_cache)

        # Track active combat for next tick
        has_combat = False
        if any(p.fighting for p in room.players):
            has_combat = True
        elif any(m.fighting for m in room.monsters):
            has_combat = True
            
        if has_combat:
            next_active_ids.add(room.id)

    # [REMOVED] Reaper and Flush handled by High-Res Pulse in godless_mud.py

    _ACTIVE_COMBAT_ROOM_IDS = next_active_ids
    # logger.debug("process_round complete")

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

    # 2. Mob Specific AI/Behavior (Pre-Validation handled by Event)
    # Event subscribed by logic/core/systems/ai.py

    # 3. Validation & Targeting
    target = combatant.fighting # Re-fetch in case changed
    
    # Unified validation using Facade
    if not combat.is_target_valid(combatant, target):
        target = combat.handle_target_loss(combatant)
        if not target:
            players_to_prompt.add(combatant)
            return

    # Visibility Check with Caching (Processor maintains cache for performant rounds)
    can_see_target = False
    if visibility_cache is not None:
        cache_key = (combatant, target)
        if cache_key not in visibility_cache:
            visibility_cache[cache_key] = vision_engine.can_see(combatant, target)
        can_see_target = visibility_cache[cache_key]
    else:
        can_see_target = vision_engine.can_see(combatant, target)
    
    if not can_see_target:
        target = combat.handle_target_loss(combatant)
        if not target:
            players_to_prompt.add(combatant)
            return

    # 4. Execute Attack
    if target:
        # Check if capable of acting
        if not combat.can_act(combatant):
            return
            
        # Mob Skill Logic
        skill_to_use = ai.get_mob_skill(combatant, game)
            
        combat.handle_attack(combatant, target, room, game, blessing=skill_to_use)
        
        # 5. Event: Turn End (Post-Attack)
        end_ctx = {'entity': combatant, 'target': target, 'game': game}
        event_engine.dispatch("combat_turn_end", end_ctx)

def execute_attack(combatant, target, room, game, players_to_prompt, blessing=None):
    """Legacy wrapper for backward compatibility with base_executor."""
    combat_actions.execute_attack(combatant, target, room, game, players_to_prompt, blessing)
