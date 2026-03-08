"""
logic/modules/common/maneuvers.py
Domain: Spatial & Movement Logic.
"""
import random
from logic import search
from logic.commands.info import exploration as information
from logic.commands import movement_commands as movement
from logic.actions.registry import register
from logic.actions.skill_utils import _apply_damage
from logic.common import get_reverse_direction
from logic.core import status_effects_engine
from logic.core import resource_engine
from logic.calibration import ScalingRules
from utilities.colors import Colors
from .utility import _consume_resources

@register("drag")
def handle_drag(player, skill, args, target=None):
    """
    Drag: Pulls a target from the current room to an adjacent room.
    """
    if not args:
        player.send_line("Drag whom where? (drag <target> <direction>)")
        return None, True

    parts = args.split()
    if len(parts) < 2:
        if player.fighting and parts[0] in player.room.exits:
            target = player.fighting
            direction = parts[0]
        else:
            player.send_line("Usage: drag <target> <direction>")
            return None, True
    else:
        direction = parts[-1]
        target_name = " ".join(parts[:-1])
        target = search.find_living(player.room, target_name)

    if not target:
        player.send_line("You don't see them here.")
        return None, True
        
    if target == player:
        player.send_line("You cannot drag yourself.")
        return None, True

    direction = direction.lower()
    mapping = {'n': 'north', 's': 'south', 'e': 'east', 'w': 'west', 'u': 'up', 'd': 'down'}
    direction = mapping.get(direction, direction)
    
    if direction not in player.room.exits:
        player.send_line(f"You cannot drag them {direction} (invalid exit).")
        return None, True

    dest_room = player.game.world.rooms.get(player.room.exits[direction])
    if not dest_room:
        player.send_line("That path is blocked.")
        return None, True

    old_room = player.room
    
    if player in old_room.players: old_room.players.remove(player)
    player.room = dest_room
    dest_room.players.append(player)
    
    if target in old_room.players: old_room.players.remove(target)
    elif target in old_room.monsters: old_room.monsters.remove(target)
    
    target.room = dest_room
    if hasattr(target, 'send_line'): dest_room.players.append(target)
    else: dest_room.monsters.append(target)
    
    player.send_line(f"{Colors.RED}You drag {target.name} {direction}!{Colors.RESET}")
    old_room.broadcast(f"{player.name} drags {target.name} {direction}!", exclude_player=player)
    dest_room.broadcast(f"{player.name} drags {target.name} in from the {get_reverse_direction(direction)}.", exclude_player=player)
    
    if hasattr(target, 'send_line'):
        target.send_line(f"{Colors.RED}{player.name} drags you {direction}!{Colors.RESET}")
        information.look(target, "")
        
    information.look(player, "")
    
    if not player.fighting:
        player.fighting = target
        player.state = "combat"
    if not target.fighting:
        target.fighting = player
        if hasattr(target, 'state'): target.state = "combat"
        
    _consume_resources(player, skill)
    return target, True

@register("charge")
def handle_charge(player, skill, args, target=None):
    """
    Charge: Rush into a room or at a target to initiate combat with bonus damage.
    """
    if not args:
        player.send_line("Charge at whom or which direction?")
        return None, True
        
    parts = args.split()
    direction = parts[0].lower()
    
    if direction in player.room.exits:
        if len(parts) < 2:
            player.send_line("Charge at whom in that direction?")
            return None, True
        target_name = " ".join(parts[1:])
        old_room = player.room
        movement._move(player, direction)
        if player.room == old_room: return None, True
        target = search.find_living(player.room, target_name)
    else:
        target = search.find_living(player.room, args)
        
    if not target:
        player.send_line(f"You charged in, but don't see '{args}' here!")
        return None, True
        
    if target == player:
        player.send_line("You cannot charge yourself.")
        return None, True

    # --- Total Mass Check (Auditor Logic Hook) ---
    # Calculate total carried weight (Inventory + Equipment)
    total_weight = sum(getattr(i, 'weight', 0) for i in player.inventory)
    equipped_items = [
        getattr(player, 'equipped_weapon', None),
        getattr(player, 'equipped_offhand', None),
        getattr(player, 'equipped_armor', None)
    ]
    total_weight += sum(getattr(i, 'weight', 0) for i in equipped_items if i)

    # Apply Heavy Penalty if over threshold
    if total_weight > ScalingRules.HEAVY_WEIGHT_THRESHOLD:
        penalty = 10
        resource_engine.modify_resource(player, "stamina", -penalty, source="Overburdened Charge")
        player.send_line(f"{Colors.YELLOW}[Heavy] Your weight makes the charge exhausting (-{penalty} Stamina).{Colors.RESET}")

    # --- Breakage Physics ---
    # 5% chance to damage equipment
    if random.random() < 0.05:
        valid_gear = [i for i in equipped_items if i and hasattr(i, 'integrity')]
        if valid_gear:
            target_item = random.choice(valid_gear)
            target_item.integrity -= 1
            player.send_line(f"{Colors.YELLOW}Your {target_item.name} shudders from the impact!{Colors.RESET}")
            
            # Breakage Consequence
            if target_item.integrity <= 0:
                target_item.integrity = 0
                player.send_line(f"{Colors.RED}Your {target_item.name} has broken! Its stats are ruined.{Colors.RESET}")
                
                # Nerf Stats
                if hasattr(target_item, 'defense'):
                    target_item.defense = 1
                if hasattr(target_item, 'damage_dice'):
                    target_item.damage_dice = "1d2" # Effectively 1 damage

    # Execute Charge
    player.send_line(f"{Colors.RED}You slam into {target.name} with incredible momentum!{Colors.RESET}")
    player.room.broadcast(f"{player.name} charges into {target.name}!", exclude_player=player)
    _apply_damage(player, target, 15, "Charge")
    _consume_resources(player, skill)
    return target, True

@register("push")
def handle_push(player, skill, args, target=None):
    """
    Push: Forcefully shove an enemy into an adjacent room.
    """
    parts = args.split()
    if not parts:
        player.send_line("Push whom where? (push <target> <direction>)")
        return None, True
    
    directions = ["north", "south", "east", "west", "up", "down", "n", "s", "e", "w", "u", "d"]
    mapping = {'n': 'north', 's': 'south', 'e': 'east', 'w': 'west', 'u': 'up', 'd': 'down'}
    
    target_name, direction = "", ""
    if len(parts) > 1 and parts[-1].lower() in directions:
        direction = mapping.get(parts[-1].lower(), parts[-1].lower())
        target_name = " ".join(parts[:-1])
    else:
        target_name = " ".join(parts)
        
    target = search.find_living(player.room, target_name)
    if not target:
        player.send_line(f"You don't see '{target_name}' here.")
        return None, True
    
    if target == player:
        player.send_line("You cannot push yourself.")
        return None, True

    if not direction:
        # If no direction provided, pick a random valid exit
        if player.room.exits:
            direction = random.choice(list(player.room.exits.keys()))
        else:
            player.send_line("There's nowhere to push them!")
            return target, True
            
    if direction not in target.room.exits:
        player.send_line(f"You can't push them {direction} from here.")
        return target, True

    # Actual Push Logic
    old_room = target.room
    dest_room_id = old_room.exits[direction]
    dest_room = player.game.world.rooms.get(dest_room_id)
    
    if not dest_room:
        player.send_line("That path is blocked.")
        return target, True

    # Move Target
    if target in old_room.players: old_room.players.remove(target)
    elif target in old_room.monsters: old_room.monsters.remove(target)
    
    target.room = dest_room
    if hasattr(target, 'send_line'): dest_room.players.append(target)
    else: dest_room.monsters.append(target)
    
    player.send_line(f"{Colors.RED}You forcefully push {target.name} {direction}!{Colors.RESET}")
    old_room.broadcast(f"{player.name} pushes {target.name} {direction}!", exclude_player=player)
    dest_room.broadcast(f"{target.name} is pushed in from the {get_reverse_direction(direction)}!", exclude_player=None)
    
    if hasattr(target, 'send_line'):
        target.send_line(f"{Colors.RED}{player.name} pushes you {direction}!{Colors.RESET}")
        information.look(target, "")

    _consume_resources(player, skill)
    return target, True


@register("struggle")
def handle_struggle(player, skill, args, target=None):
    # Logic migrated from defensive.py
    return None, True