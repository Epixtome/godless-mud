import logic.handlers.command_manager as command_manager
from logic.commands import skill_commands
from utilities.colors import Colors

@command_manager.register("cast", category="combat")
def cast(player, args):
    """
    Cast a spell.
    Usage: cast <spell name> [target]
    """
    if not args:
        player.send_line("Cast what?")
        return

    # Parse args (spell name vs target)
    # Heuristic: Check if the first word matches a known spell, or first 2 words, etc.
    # Since we don't have a strict spell list, we iterate known blessings.
    
    parts = args.split()
    spell = None
    target_args = ""
    
    # Try to match spell name from start of string
    for i in range(len(parts), 0, -1):
        potential_name = " ".join(parts[:i]).lower().replace(" ", "_")
        for b_id in player.equipped_blessings:
            if b_id == potential_name or b_id.startswith(potential_name):
                spell = player.game.world.blessings.get(b_id)
                target_args = " ".join(parts[i:])
                break
        if spell: break
    
    if not spell:
        player.send_line("You do not have that blessing equipped in your deck.")
        return

    # Execute using the central skill logic
    skill_commands._execute_skill(player, spell, target_args)
