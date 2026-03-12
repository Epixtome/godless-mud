from logic.handlers import command_manager
from logic.core import search
from utilities.colors import Colors

@command_manager.register("talk", "interact", category="social")
def talk_to_npc(player, args):
    """Start a conversation with an NPC."""
    if not args:
        player.send_line("Talk to whom?")
        return
        
    npc = search.find_living(player.room, args)
    if not npc:
        player.send_line("You don't see them here.")
        return
        
    # Check if NPC has dialogue or interaction capabilities
    if not hasattr(npc, 'dialogue') and not "quest_giver" in npc.tags and not "shopkeeper" in npc.tags:
        player.send_line(f"{npc.name} doesn't seem to have much to say.")
        return
        
    # Enter Interaction Mode
    player.state = "interaction"
    player.interaction_data = {
        'type': 'dialogue',
        'target_id': npc.prototype_id if hasattr(npc, 'prototype_id') else None,
        'target_name': npc.name,
        'npc': npc,
        'node': 'start'
    }
    
    # Trigger initial display
    from logic.engines import interaction_engine
    interaction_engine.display_dialogue(player)
