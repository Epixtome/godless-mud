"""
Handles the lifecycle transitions of combat entities (Death, Respawn, Corpse creation).
Decouples the 'aftermath' of combat from the real-time processing loop.
"""
import logging
import asyncio
from models import Corpse, Monster, Player
from logic import mob_manager
from logic.core import combat
from logic.core import event_engine
from utilities.colors import Colors

logger = logging.getLogger("GodlessMUD")

def handle_death(game, victim, killer):
    """
    Public entry point to handle entity death.
    Routes to specific handlers based on entity type.
    """
    # --- DEFERRED DEATH PROTOCOL (V4.5) ---
    logger.debug(f"[DEATH_TRACE] handle_death called for {victim.name} (HP: {victim.hp}). Pending: {getattr(victim, 'pending_death', False)}")

    # To prevent race conditions during synchronous execution, we flag the entity
    # for death and add them to a deferred queue for cleanup at the end of the tick.
    if getattr(victim, 'pending_death', False):
        logger.debug(f"[DEATH_TRACE] Skipping {victim.name} - already pending death.")
        return

    # Resilience: Attempt to recover the game object if None was passed
    if game is None:
        game = getattr(victim, 'game', None)

    if game is None:
        # Critical Fallback: If no game reference exists, process synchronously to avoid loss of state
        logger.warning(f"[DEATH] Game reference missing for {victim.name}. Processing synchronously.")
            
        # [FIX] Ensure we flag as dead even in synchronous mode to prevent double-processing
        victim.pending_death = True
            
        if isinstance(victim, Player):
            _handle_player_death(None, victim, killer)
        else:
            _handle_mob_death(None, victim, killer)
        return

    victim.pending_death = True
    if not hasattr(game, 'dead_entities'):
        game.dead_entities = []
    
    # Store the kill context for the cleanup phase
    game.dead_entities.append({
        'victim': victim,
        'killer': killer,
        'tick': game.tick_count
    })
    
    # Immediate visual feedback (Optional, but helps with 'feel')
    if isinstance(victim, Monster):
        logger.debug(f"[DEATH] {victim.name} flagged for deferred cleanup.")
    elif isinstance(victim, Player):
        logger.debug(f"[DEATH] {victim.name} flagged for deferred resurrection.")

def process_dead_queue(game):
    """
    The Reaper: Processes all entities flagged for death during this tick.
    Must be called at the end of the game loop/tick or after async actions.
    """
    if not hasattr(game, 'dead_entities') or not game.dead_entities:
        return []

    # Process copy of list to allow safe modification
    queue = game.dead_entities[:]
    game.dead_entities = []
    logger.debug(f"[REAPER] Processing {len(queue)} dead entities.")
    for context in queue:
        victim = context['victim']
        killer = context['killer']
        
        try:
            if isinstance(victim, Player):
                _handle_player_death(game, victim, killer)
            else:
                _handle_mob_death(game, victim, killer)
        except Exception as e:
            logger.error(f"[REAPER] Error processing death for {victim.name}: {e}")
            import traceback
            logger.error(traceback.format_exc())

def _handle_mob_death(game, mob, killer):
    """Handles logic when a monster dies."""
    room = mob.room
    if not room:
        logger.error(f"Mob {mob.name} died but has no room reference.")
        return

    # Create corpse (Preserves tags for sacrifice/favor logic)
    corpse = Corpse(f"corpse of {mob.name}", f"The dead body of {mob.name}.", mob.inventory, tags=getattr(mob, 'tags', []))
    room.items.append(corpse)
    room.dirty = True
    
    # Register Decay
    try:
        from logic import systems
        systems.register_decay(game, corpse, room)
    except Exception as e:
        logger.error(f"Failed to register decay for {mob.name}: {e}")
    
    if mob in room.monsters:
        room.monsters.remove(mob)
        
    # Stop Combat (Clear references via Model logic)
    mob.die()
    
    # Modular Hook for death reactions (Quests, Beastmaster penalties, etc)
    from logic.core import event_engine
    event_engine.dispatch("on_mob_death", mob=mob, killer=killer)
    
    # Notify mob manager for respawn
    if game:
        mob_manager.notify_death(game, mob)
    
    # Player specific rewards (Moved back to deferred phase for correct ordering)
    if isinstance(killer, Player):
        killer.send_line(f"{Colors.BOLD}{Colors.YELLOW}You have defeated {mob.name}!{Colors.RESET}")
        room.broadcast(f"{Colors.YELLOW}{mob.name} has been defeated by {killer.name}!{Colors.RESET}", exclude_player=killer)
        
        # Notify quest system
        if hasattr(killer, 'active_quests'):
            from logic.core import quests
            quests.update_kill_progress(killer, mob.prototype_id)
            
        # Distribute Rewards
        if game:
            from logic.core import combat
            combat.distribute_rewards(killer, mob, game)

    elif isinstance(killer, Monster) and killer.leader and isinstance(killer.leader, Player):
        # Companion Kill: Reward the leader
        killer.leader.send_line(f"{Colors.BOLD}{Colors.YELLOW}Your companion {killer.name} has defeated {mob.name}!{Colors.RESET}")
        room.broadcast(f"{Colors.YELLOW}{mob.name} has been defeated by {killer.name}!{Colors.RESET}", exclude_player=killer.leader)
        if game:
             from logic.core import combat
             combat.distribute_rewards(killer.leader, mob, game)
    else:
        # Non-player kill (e.g. mob vs mob)
        room.broadcast(f"{Colors.YELLOW}{mob.name} has been defeated!{Colors.RESET}")

    
def _handle_player_death(game, player, killer):
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
    room.dirty = True
    room.broadcast(f"{player.name} falls dead, dropping to the ground.", exclude_player=player)
    
    # Register Decay
    from logic import systems
    systems.register_decay(game, p_corpse, room)
    
    # 2. Resurrect at start room
    player.hp = player.max_hp
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
    from logic.handlers import input_handler
    input_handler.handle(player, "look")

def _on_death_event(ctx):
    """Event listener for entity death."""
    victim = ctx.get('victim')
    killer = ctx.get('killer')
    # Recover game reference from the entity since events are stateless
    game = getattr(victim, 'game', None)
    handle_death(game, victim, killer)

# Subscribe to the global event bus
event_engine.subscribe("on_death", _on_death_event)
