from logic.handlers import command_manager
from logic import search
from models import Monster
import logging

logger = logging.getLogger("GodlessMUD")

@command_manager.register("say", "'", category="social")
def say(player, args):
    """Say something to the room."""
    if not args:
        player.send_line("Say what?")
        return
    
    player.send_line(f"You say: '{args}'")
    player.room.broadcast(f"{player.name} says: '{args}'", exclude_player=player)

@command_manager.register("emote", ":", category="social")
def emote(player, args):
    """Perform an action."""
    if not args:
        player.send_line("Emote what?")
        return
        
    player.room.broadcast(f"{player.name} {args}")
    player.send_line(f"{player.name} {args}")

@command_manager.register("gift", category="social")
def gift(player, args):
    """Give an item to an NPC to build friendship."""
    if not args:
        player.send_line("Gift what to whom? (Usage: gift <item> <npc>)")
        return
        
    parts = args.split()
    if len(parts) < 2:
        player.send_line("Usage: gift <item> <npc>")
        return
        
    item_name = parts[0]
    npc_name = " ".join(parts[1:])
    
    # Find Item
    item = search.search_list(player.inventory, item_name)
    if not item:
        player.send_line("You don't have that item.")
        return
        
    # Find NPC
    npc = search.find_living(player.room, npc_name)
    if not npc or not isinstance(npc, Monster):
        player.send_line("You don't see them here.")
        return
        
    if not npc.can_be_companion:
        player.send_line(f"{npc.name} cannot be recruited as a companion.")
        return
        
    # Process Gift
    player.inventory.remove(item)
    player.room.broadcast(f"{player.name} gives {item.name} to {npc.name}.", exclude_player=player)
    player.send_line(f"You give {item.name} to {npc.name}.")
    
    # Increase Friendship
    current = player.friendship.get(npc.prototype_id, 0)
    gain = max(1, item.value // 10) # Value-based gain
    new_val = min(100, current + gain)
    player.friendship[npc.prototype_id] = new_val
    
    player.send_line(f"{npc.name} looks pleased. (Friendship: {new_val}/100)")
    
    if new_val >= 50 and current < 50:
        player.send_line(f"{npc.name} trusts you enough to join you! (Use @recruit for now, real command coming soon)")

logger.info("Social module loaded.")