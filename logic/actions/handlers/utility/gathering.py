"""
logic/actions/handlers/utility/gathering.py
Resource collection: Harvest / Gather.
"""
from logic.actions.registry import register
from logic.common import find_by_index
from logic.engines import action_manager
from utilities.colors import Colors

def _consume(player, skill):
    from logic.engines import magic_engine
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)
    magic_engine.consume_pacing(player, skill)

@register("harvest", "gather")
def handle_harvest(player, skill, args, target=None):
    resource_node = None
    if args:
        resource_node = find_by_index(player.room.items, args)
    else:
        for item in player.room.items:
            if hasattr(item, 'flags') and "resource" in item.flags:
                resource_node = item
                break
    
    if not resource_node:
        player.send_line("There is nothing here to harvest.")
        return None, True

    player.send_line(f"You begin harvesting {resource_node.name}...")
    
    async def _finish_harvest():
        player.send_line(f"{Colors.GREEN}You successfully harvest materials from {resource_node.name}.{Colors.RESET}")
        player.send_line(f"{Colors.CYAN}You find some raw materials!{Colors.RESET}")
        
    action_manager.start_action(player, 3.0, _finish_harvest, tag="harvesting", fail_msg="Harvesting interrupted.")
    _consume(player, skill)
    return None, True
