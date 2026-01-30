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
        player.send_line("  list            - List blessings available.")
        player.send_line("  buy <id>        - Purchase a blessing.")
        player.send_line("  memorize <id>   - Equip a blessing.")
        player.send_line("  forget <id>     - Unequip a blessing.")
        player.send_line("  deck            - View equipped deck.")
        player.send_line("  exit            - Leave the trance.")
        
    elif cmd == 'list':
        player.send_line(f"\n{Colors.BOLD}=== Blessings of {deity_name} ==={Colors.RESET}")
        player.send_line(f"Current Favor: {Colors.CYAN}{player.favor.get(deity_id, 0)}{Colors.RESET}")
        
        by_tier = {1: [], 2: [], 3: [], 4: []}
        for b in player.game.world.blessings.values():
            if getattr(b, 'deity_id', None) == deity_id:
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
                    status = f"{Colors.YELLOW}[Buy]{Colors.RESET}" if can_afford else f"{Colors.RED}[Locked]{Colors.RESET}"
                    price = f"{b.cost} Favor"
                    name_color = Colors.YELLOW if can_afford else Colors.WHITE
                
                player.send_line(f"{status} {name_color}{b.name:<20}{Colors.RESET} : {price}")
                player.send_line(f"      {Colors.CYAN}ID:{Colors.RESET} {b.id}")
                player.send_line(f"      {Colors.WHITE}{b.description}{Colors.RESET}")

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
            
        cost = blessing.cost
        current_favor = player.favor.get(deity_id, 0)
        if current_favor < cost:
            player.send_line(f"You need {cost} favor, but only have {current_favor}.")
            return
            
        player.favor[deity_id] -= cost
        player.known_blessings.append(b_id)
        player.send_line(f"You have learned {Colors.BOLD}{blessing.name}{Colors.RESET}!")
        class_engine.check_unlocks(player)

    elif cmd == 'memorize' or cmd == 'mem':
        if not args:
            player.send_line("Memorize what? (memorize <id>)")
            return
        b_id = args[0].lower()
        if b_id not in player.known_blessings:
            player.send_line("You do not know that blessing.")
            return
        if b_id not in player.equipped_blessings:
            player.equipped_blessings.append(b_id)
            player.send_line(f"You memorize {b_id}.")
            class_engine.calculate_identity(player)
            synergy_engine.calculate_synergies(player)
        else:
            player.send_line("Already memorized.")

    elif cmd == 'forget':
        if not args:
            player.send_line("Forget what? (forget <id>)")
            return
        b_id = args[0].lower()
        if b_id in player.equipped_blessings:
            player.equipped_blessings.remove(b_id)
            player.send_line(f"You forget {b_id}.")
            class_engine.calculate_identity(player)
            synergy_engine.calculate_synergies(player)
        else:
            player.send_line("That is not in your deck.")
            
    elif cmd == 'deck':
        # Allow checking deck inside trance
        from logic.actions.deck import deck
        deck(player, "")
        
    else:
        player.send_line("Unknown command. Type 'help' or 'exit'.")