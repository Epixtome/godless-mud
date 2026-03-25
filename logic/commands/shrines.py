"""
logic/commands/shrines.py
Player-facing commands for interacting with divine shrines.
"""
from utilities.colors import Colors
import logic.handlers.command_manager as command_manager
from logic.core.systems.influence_service import InfluenceService

@command_manager.register("sacrifice", category="divine")
def sacrifice_command(player, args):
    """
    Sacrifice items or corpses to a deity at a shrine.
    Usage: sacrifice <item_name>
    Usage: sacrifice corpse
    """
    if not args:
        player.send_line("Usage: sacrifice <item_name> or sacrifice corpse")
        return

    # 1. Check for shrine presence
    influence_service = InfluenceService.get_instance()
    x, y, z = player.room.x, player.room.y, player.room.z
    shrine = None
    for s in influence_service.shrines.values():
        if s.coords[0] == x and s.coords[1] == y and s.coords[2] == z:
            shrine = s
            break
    
    if not shrine:
        player.send_line("You must be at a divine shrine to perform a sacrifice.")
        return

    # 2. Identify Target Item
    item_name = args.lower()
    target_item = None
    
    if item_name == "corpse":
        # Find any corpse in the room
        for item in player.room.items:
            if hasattr(item, 'prototype_id') and item.prototype_id == "corpse":
                target_item = item
                break
        if not target_item:
            player.send_line("There are no corpses here to sacrifice.")
            return
    else:
        # Search inventory
        for item in player.inventory:
            if item.name.lower() == item_name:
                target_item = item
                break
        if not target_item:
            player.send_line(f"You don't have a '{args}' to sacrifice.")
            return

    # 3. Calculate Favor Value
    # Base calculation: Rarity/Value for items, or Mob Level for corpses.
    base_favor = 0
    if item_name == "corpse":
        mob_level = getattr(target_item, 'mob_level', 5)
        base_favor = 20 + (mob_level * 5)
    else:
        value = getattr(target_item, 'value', 10)
        rarity = getattr(target_item, 'rarity', 'common').lower()
        rarity_mults = {"common": 1, "uncommon": 2, "rare": 5, "epic": 15, "legendary": 50}
        base_favor = (value // 10) * rarity_mults.get(rarity, 1)

    # 4. Apply Kingdom Scaling (V7.2)
    multiplier = 1.0
    if shrine.captured_by == player.kingdom:
        multiplier = 1.2 # Kingdom Loyalty Bonus
        player.send_line(f"{Colors.GREEN}Divine Resonance: Sacrificing to your kingdom's shrine yields extra favor!{Colors.RESET}")
    elif shrine.captured_by and shrine.captured_by != "neutral" and shrine.captured_by != player.kingdom:
        multiplier = 0.5 # Contrariety Penalty
        player.send_line(f"{Colors.RED}The altar rejects your foreign offering. Favor gain reduced.{Colors.RESET}")

    final_favor = int(base_favor * multiplier)

    # 5. Execute Sacrifice
    from logic.core.services import favor_service
    favor_service.award_favor(player, shrine.deity_id, final_favor)
    
    # Remove item
    if item_name == "corpse":
        player.room.items.remove(target_item)
        player.room.broadcast(f"{Colors.CYAN}{player.name} offers a fallen foe to {shrine.name}.{Colors.RESET}", exclude_player=player)
    else:
        player.inventory.remove(target_item)
        player.room.broadcast(f"{Colors.CYAN}{player.name} offers {target_item.name} to {shrine.name}.{Colors.RESET}", exclude_player=player)

    player.send_line(f"{Colors.BOLD}{Colors.YELLOW}The altar blazes as your offering is consumed!{Colors.RESET}")

@command_manager.register("ritual", category="divine")
def ritual_command(player, args):
    """
    Perform a divine ritual at a shrine.
    Usage: ritual blessing <class_id>
    Usage: ritual claim (Admin/Siege Phase Only)
    """
    if not args:
        player.send_line("Usage: ritual blessing <class_id>")
        return

    parts = args.split()
    action = parts[0].lower()

    if action == "blessing":
        if len(parts) < 2:
            player.send_line("Usage: ritual blessing <class_id>")
            return
        
        target_class = parts[1].lower()
        
        # Check shrine
        influence_service = InfluenceService.get_instance()
        x, y, z = player.room.x, player.room.y, player.room.z
        shrine = None
        for s in influence_service.shrines.values():
            if s.coords[0] == x and s.coords[1] == y and s.coords[2] == z:
                shrine = s
                break
        
        if not shrine:
            player.send_line("You must be at a divine shrine to perform a blessing ritual.")
            return

        # Check deity
        from logic.core.services import deity_service
        deities = deity_service.get_deities()
        
        if target_class not in [c for d in deities.values() for c in d.get('granted_classes', [])]:
            # Fallback if class not in deities list yet
            pass
        
        base_cost = 500
        
        # Scaling Cost (Kingdom Check)
        multiplier = 1.5
        if shrine.captured_by == player.kingdom:
            multiplier = 0.5 # 50% discount for matching kingdom
        
        total_cost = int(base_cost * multiplier)
        
        # Execute Class Swap (placeholder for full kit logic)
        from logic.core.services import favor_service
        if favor_service.unlock_class(player, shrine.deity_id, total_cost, target_class):
            player.send_line(f"{Colors.CYAN}The Blessing Ritual is complete! You are now a {target_class.title()}.{Colors.RESET}")
            player.load_kit(target_class) # Apply the GCA 8-ability kit
        else:
            player.send_line(f"{Colors.RED}You lack the {total_cost} Favor with {shrine.deity_id.title()} required for this blessing.{Colors.RESET}")

    elif action == "claim":
        # Check for shrine presence (redundant but safe)
        service = InfluenceService.get_instance()
        # Find shrine here
        shrine = next((s for s in service.shrines.values() if s.coords == [player.room.x, player.room.y, player.room.z]), None)
        
        if not shrine:
            player.send_line("There is no sanctuary anchor here to claim.")
            return

        if shrine.captured_by != "neutral" and shrine.captured_by != player.kingdom:
            player.send_line(f"This sanctuary resonance is currently held by the Kingdom of {shrine.captured_by.title()}. BREAK it first!")
            return
            
        if shrine.captured_by == player.kingdom:
            player.send_line(f"Your kingdom already holds this sanctuary. Your favor cost for rituals is already discounted.")
            return

        # V7.2: Perform the Claim
        # Requirements: We might want a favor cost for claiming too? 
        # For now, let's make it FREE to encourage capture, but it resets potency to a low base
        shrine.captured_by = player.kingdom
        shrine.potency = 500 # Re-stabilize at 50% of nominal outposts
        
        # Save to disk using the construction facade (to avoid circular imports, late import)
        from logic.commands.admin.construction.shrine_admin import save_shrine_to_disk
        save_shrine_to_disk(shrine)
        service.clear_cache()
        
        # Notify the room
        player.send_line(f"{Colors.GREEN}You have bound the Sanctuary of {shrine.deity_id.title()} to the Kingdom of {player.kingdom.title()}!{Colors.RESET}")
        player.room.broadcast(f"{player.name} performs a ritual, claiming this sanctuary for the {player.kingdom.title()}!", exclude_player=player)
        
        # [GLOBAL BROADCAST]
        msg = f"{Colors.BOLD}{Colors.YELLOW}[SOVEREIGNTY]{Colors.RESET} {Colors.WHITE}The Kingdom of {player.kingdom.title()} has claimed the Sanctuary of {shrine.deity_id.title()}!{Colors.RESET}"
        if player.game:
            player.game.broadcast(msg)
