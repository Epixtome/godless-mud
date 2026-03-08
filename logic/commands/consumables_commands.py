from logic.handlers import command_manager
from models import Consumable

@command_manager.register("quaff", "drink", category="item")
def quaff(player, args):
    """Drink a potion or consumable."""
    if not args:
        player.send_line("Quaff what?")
        return
    
    # Search inventory
    target_item = None
    for item in player.inventory:
        if isinstance(item, Consumable) and (args.lower() in item.name.lower()):
            target_item = item
            break
    
    if not target_item:
        player.send_line("You don't have that.")
        return
    
    # Apply effects
    msg = []
    for effect, amount in target_item.effects.items():
        if effect == 'hp':
            old_hp = player.hp
            player.hp = min(player.max_hp, player.hp + amount)
            actual_heal = player.hp - old_hp
            msg.append(f"heals you for {actual_heal} HP")
        elif effect in player.resources:
            player.resources[effect] += amount
            msg.append(f"restores {amount} {effect.title()}")
        
    # Remove item
    player.inventory.remove(target_item)
    
    if msg:
        player.send_line(f"You quaff {target_item.name}. It {', '.join(msg)}.")
        player.room.broadcast(f"{player.name} quaffs {target_item.name}.", exclude_player=player)
    else:
        player.send_line(f"You quaff {target_item.name}, but nothing happens.")