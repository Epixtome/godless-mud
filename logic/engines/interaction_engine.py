from utilities.colors import Colors
from logic.engines import class_engine
from logic.engines import synergy_engine

def dispatch(player, command):
    """
    Routes input for players in the 'interaction' state.
    Returns True to indicate the input was handled.
    """
    data = getattr(player, 'interaction_data', {})
    i_type = data.get('type')
    
    if i_type == 'commune':
        _handle_commune(player, command, data)
        return True
    else:
        player.send_line("You are in an unknown interaction state. Type 'exit' to break free.")
        if command.lower() == 'exit':
            player.state = "normal"
            player.interaction_data = {}
        return True

def _handle_commune(player, command, data):
    deity_id = data.get('deity_id')
    deity_name = data.get('deity_name')
    
    parts = command.split()
    cmd = parts[0].lower()
    args = parts[1:] if len(parts) > 1 else []
    
    if cmd == 'exit' or cmd == 'quit':
        player.send_line(f"You break your communion with {deity_name}.")
        player.state = "normal"
        player.interaction_data = {}
        return
        
    elif cmd == 'help':
        player.send_line(f"{Colors.BOLD}Commune Commands:{Colors.RESET}")
        player.send_line("  list blessings  - List blessings available.")
        player.send_line("  list classes    - List classes available from this deity.")
        player.send_line("  buy <id>        - Purchase a blessing.")
        player.send_line("  become <id>     - Adopt a class archetype (Costs 250 Favor).")
        player.send_line("  deck            - View currently active blessings.")
        player.send_line("  exit            - Leave the trance.")
        
    elif cmd == 'list':
        sub = args[0].lower() if args else "blessings"
        
        if sub == 'blessings':
            player.send_line(f"\n{Colors.BOLD}=== Blessings of {deity_name} ==={Colors.RESET}")
            player.send_line(f"Current Favor: {Colors.CYAN}{player.favor.get(deity_id, 0)}{Colors.RESET}")
            
            by_tier = {1: [], 2: [], 3: [], 4: []}
            for b in player.game.world.blessings.values():
                b_deity = getattr(b, 'deity_id', None)
                if b_deity == deity_id or b_deity == 'common':
                    by_tier[b.tier].append(b)
                    
            for tier in range(1, 5):
                if not by_tier[tier]: continue
                player.send_line(f"\n{Colors.BOLD}{Colors.WHITE}--- Tier {tier} ---{Colors.RESET}")
                for b in sorted(by_tier[tier], key=lambda x: x.cost):
                    if b.id in player.known_blessings:
                        status = f"{Colors.GREEN}[Owned]{Colors.RESET}"
                        price = "---"
                        name_color = Colors.GREEN
                    else:
                        can_afford = player.favor.get(deity_id, 0) >= b.cost
                        
                        # Check Class Requirement
                        req_class = getattr(b, 'required_class', None)
                        class_match = True
                        if req_class:
                            if player.active_class != req_class.lower():
                                # Check name match too
                                active_cls_obj = player.game.world.classes.get(player.active_class)
                                if not active_cls_obj or active_cls_obj.name.lower() != req_class.lower():
                                    class_match = False

                        if not class_match:
                            status = f"{Colors.RED}[Class]{Colors.RESET}"
                            name_color = Colors.RED
                        elif can_afford:
                            status = f"{Colors.YELLOW}[Buy]{Colors.RESET}"
                            name_color = Colors.YELLOW
                        else:
                            status = f"{Colors.RED}[Favor]{Colors.RESET}"
                            name_color = Colors.WHITE
                        
                        price = f"{b.cost} Favor"
                    
                    player.send_line(f"{status} {name_color}{b.name:<20}{Colors.RESET} : {price}")
                    player.send_line(f"      {Colors.CYAN}ID:{Colors.RESET} {b.id}")
                    player.send_line(f"      {Colors.WHITE}{b.description}{Colors.RESET}")
        
        elif sub == 'classes' or sub == 'kits':
            player.send_line(f"\n{Colors.BOLD}=== Archetypes of {deity_name} ==={Colors.RESET}")
            
            # Get Deity Data from world (meta)
            d_meta = {}
            if isinstance(player.game.world.deities, dict):
                d_meta = player.game.world.deities.get(deity_id, {})
            else:
                for d in player.game.world.deities:
                    if d.get('id') == deity_id:
                        d_meta = d
                        break

            granted = d_meta.get('granted_classes', [])
            if not granted:
                player.send_line(f"{deity_name} grants no specific class archetypes.")
                return

            for cls_id in granted:
                # Use globally loaded kits from world
                kit_data = player.game.world.kits.get(cls_id, {})
                
                name = kit_data.get('name', cls_id.capitalize())
                desc = kit_data.get('description', "No description available.")
                
                status = f"{Colors.YELLOW}[Become]{Colors.RESET}"
                if player.active_class == cls_id:
                    status = f"{Colors.GREEN}[Current]{Colors.RESET}"
                
                player.send_line(f"{status} {Colors.BOLD}{name}{Colors.RESET}")
                player.send_line(f"      {Colors.WHITE}{desc}{Colors.RESET}")
                player.send_line(f"      {Colors.CYAN}ID:{Colors.RESET} {cls_id} | {Colors.YELLOW}Cost: 250 Favor{Colors.RESET}")

    elif cmd == 'buy':
        if not args:
            player.send_line("Buy what? (buy <id>)")
            return
        b_id = args[0].lower()
        
        if b_id in player.known_blessings:
            player.send_line("You already know that blessing.")
            return
            
        blessing = player.game.world.blessings.get(b_id)
        if not blessing or getattr(blessing, 'deity_id', None) != deity_id:
            player.send_line("That blessing is not available here.")
            return
            
        # Check Class Requirement
        req_class = getattr(blessing, 'required_class', None)
        if req_class:
            active_cls = player.game.world.classes.get(player.active_class) if player.active_class else None
            # Check against ID or Name (case-insensitive)
            match = False
            if active_cls:
                if active_cls.id.lower() == req_class.lower() or active_cls.name.lower() == req_class.lower():
                    match = True
            
            if not match:
                player.send_line(f"You must be a {Colors.BOLD}{req_class.replace('_', ' ').title()}{Colors.RESET} to learn this.")
                return
        
        # Check Blessing Prerequisite
        req_blessing = getattr(blessing, 'required_blessing', None)
        if req_blessing and req_blessing not in player.known_blessings:
            req_b_obj = player.game.world.blessings.get(req_blessing)
            req_name = req_b_obj.name if req_b_obj else req_blessing
            player.send_line(f"You must learn {Colors.BOLD}{req_name}{Colors.RESET} before you can learn this.")
            return
            
        cost = blessing.cost
        current_favor = player.favor.get(deity_id, 0)
        if current_favor < cost:
            player.send_line(f"You need {cost} favor, but only have {current_favor}.")
            return
            
        player.favor[deity_id] -= cost
        player.known_blessings.append(b_id)
        
        # Auto-equip if it belongs to current class and deck isn't full
        from logic.calibration import MaxValues
        if b_id not in player.equipped_blessings and len(player.equipped_blessings) < MaxValues.DECK_SIZE:
            player.equipped_blessings.append(b_id)
            player.send_line(f"You have learned and equipped {Colors.BOLD}{blessing.name}{Colors.RESET}!")
        else:
            player.send_line(f"You have learned {Colors.BOLD}{blessing.name}{Colors.RESET}! (Deck is full, use 'memorize' to swap)")
        
        class_engine.calculate_identity(player)

    elif cmd == 'become' or cmd == 'swap':
        if not args:
            player.send_line("Become what? (become <class_id>)")
            return
        cls_id = args[0].lower()
        
        if player.active_class == cls_id:
            player.send_line(f"You are already a {cls_id.capitalize()}.")
            return
            
        # Check if deity grants this class
        d_meta = {}
        if isinstance(player.game.world.deities, dict):
            d_meta = player.game.world.deities.get(deity_id, {})
        else:
            for d in player.game.world.deities:
                if d.get('id') == deity_id:
                    d_meta = d
                    break
        
        if cls_id not in d_meta.get('granted_classes', []):
            player.send_line(f"{deity_name} does not grant the secrets of the {cls_id.capitalize()}.")
            return
            
        # Check Favor (250 for class swap)
        cost = 250
        if player.favor.get(deity_id, 0) < cost:
            player.send_line(f"You need {cost} favor to adopt a new archetype, but you only have {player.favor.get(deity_id, 0)}.")
            return
            
        # Perform Swap
        success, msg = class_engine.apply_kit(player, cls_id)
        if success:
            player.favor[deity_id] -= cost
            player.send_line(f"\n{Colors.MAGENTA}{Colors.BOLD}{msg}{Colors.RESET}")
            player.send_line("Your soul and gear have been realigned for this new path.")
            # Break interaction after class swap to force fresh start
            player.state = "normal"
            player.interaction_data = {}
        else:
            player.send_line(f"Failed to adopt archetype: {msg}")

    elif cmd == 'memorize' or cmd == 'equip':
        if not args:
            player.send_line("Usage: memorize <blessing_id>")
            return
        from logic.commands.info import blessings
        blessings.memorize(player, args[0])

    elif cmd == 'forget' or cmd == 'unequip':
        if not args:
            player.send_line("Usage: forget <blessing_id>")
            return
        from logic.commands.info import blessings
        blessings.forget(player, args[0])

    elif cmd == 'deck':
        # Allow checking deck inside trance
        from logic.handlers import input_handler
        input_handler.handle(player, "deck")
        
    else:
        player.send_line("Unknown command. Type 'help' or 'exit'.")
