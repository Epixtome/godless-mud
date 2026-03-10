from utilities.colors import Colors

def handle_rest(player, args):
    """
    Toggles the resting state of the player.
    """
    if player.is_in_combat():
        player.send_line(f"{Colors.RED}You cannot rest while fighting!{Colors.RESET}")
        return

    if player.is_resting:
        player.is_resting = False
        player.send_line(f"{Colors.YELLOW}You stand up and stop resting.{Colors.RESET}")
    else:
        player.is_resting = True
        player.send_line(f"{Colors.CYAN}You sit down to rest and recover.{Colors.RESET}")
