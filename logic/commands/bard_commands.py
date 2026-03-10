import logic.handlers.command_manager as command_manager
from logic import search
from logic.engines import blessings_engine, magic_engine
from logic.core import effects
from utilities.colors import Colors

def handle_song(player, target, blessing):
    """
    Activates a Bard song.
    Applies an upkeep effect to the caster and a buff to the room.
    """
    # 1. Check for existing song
    if "song" in player.status_effects:
        player.send_line("You are already singing a song! Stop it first.")
        return False

    # 2. Apply Upkeep to Caster
    # The engine handles the resource drain based on the 'resource_cost' in JSON
    effects.apply_effect(player, "song_of_courage_upkeep", duration=600)
    
    # 3. Apply Buff to Allies in Room
    # For now, we apply it to all players. In the future, check party/friendship.
    count = 0
    for entity in player.room.players:
        # Apply a short duration buff (4s). 
        # The idea is the Bard must keep singing (Upkeep) to refresh this? 
        # Or we just apply a long buff that gets removed if the song ends?
        # For this iteration: Apply a medium duration buff (20s) representing the lingering echo.
        effects.apply_effect(entity, "song_of_courage_buff", duration=20)
        entity.send_line(f"{Colors.CYAN}{player.name}'s song fills you with courage!{Colors.RESET}")
        count += 1
        
    player.room.broadcast(f"{player.name} begins to play a rousing melody.", exclude_player=player)
    player.send_line(f"You begin the Song of Courage. (Buffed {count} allies)")
    return True

@command_manager.register("sing", category="class")
def sing(player, args):
    """
    Perform a bardic song.
    Usage: sing <song name>
    """
    if not args:
        player.send_line("Sing what?")
        return

    # Find blessing
    blessing = search.search_list(player.game.world.blessings.values(), args)
    if not blessing:
        player.send_line("You don't know that song.")
        return

    if "song" not in blessing.identity_tags:
        player.send_line(f"{blessing.name} is not a song.")
        return

    # Validation
    ok, msg = blessings_engine.Auditor.can_invoke(blessing, player)
    if not ok:
        player.send_line(msg)
        return

    # Execute
    if handle_song(player, None, blessing):
        magic_engine.consume_resources(player, blessing)
        magic_engine.set_cooldown(player, blessing)
        magic_engine.consume_pacing(player, blessing)

@command_manager.register("shh", "quiet", category="class")
def stop_singing(player, args):
    """
    Stop your current song.
    Usage: shh
    """
    # Find active song effects
    active_songs = []
    if player.status_effects:
        for eff_id in player.status_effects:
            effect = player.game.world.status_effects.get(eff_id)
            if effect and "song" in effect.get("flags", []):
                active_songs.append(eff_id)
    
    if not active_songs:
        player.send_line("You are not singing.")
        return
        
    for eff in active_songs:
        effects.remove_effect(player, eff)
    
    player.send_line("You stop singing.")
    player.room.broadcast(f"{player.name} stops playing.", exclude_player=player)
