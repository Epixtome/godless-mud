"""
Handles the lifecycle transitions of combat entities (Death, Respawn, Corpse creation).
Decouples the 'aftermath' of combat from the real-time processing loop.
"""
import logging
from models import Corpse, Monster, Player
from logic import mob_manager
from logic.engines import combat_engine, quest_engine
from utilities.colors import Colors

logger = logging.getLogger("GodlessMUD")

def handle_death(game, victim, killer):
    """
    Public entry point to handle entity death.
    Routes to specific handlers based on entity type.
    """
    if isinstance(victim, Player):
        _handle_player_death(game, victim, killer)
    elif isinstance(victim, Monster):
        _handle_mob_death(game, victim, killer)

def _handle_mob_death(game, mob, killer):
    """Handles logic when a monster dies."""
    room = mob.room
    if not room:
        logger.error(f"Mob {mob.name} died but has no room reference.")
        return

    # Create corpse
    corpse = Corpse(f"corpse of {mob.name}", f"The dead body of {mob.name}.", mob.inventory)
    room.items.append(corpse)
    room.dirty = True
    
    # Register Decay
    from logic import systems
    systems.register_decay(game, corpse, room)
    
    if mob in room.monsters:
        room.monsters.remove(mob)
        
    # Stop Combat (Clear references via Model logic)
    mob.die()
    
    # Notify mob manager for respawn
    mob_manager.notify_death(game, mob)
    
    # Player specific rewards
    if isinstance(killer, Player):
        # Notify quest system
        if hasattr(killer, 'active_quests'):
            quest_engine.update_kill_progress(killer, mob.prototype_id)
            
        # Distribute Favor
        combat_engine.distribute_favor(killer, mob, game)

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
