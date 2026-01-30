from utilities.colors import Colors

def format_damage(attacker_name, target_name, damage, source=None):
    """
    Returns (attacker_msg, target_msg, room_msg) with colored verbs.
    """
    verb = "hits"
    color = Colors.WHITE
    
    if damage <= 0:
        verb = "misses"
    elif damage < 5:
        verb = "scratches"
    elif damage < 10:
        verb = "hits"
    elif damage < 20:
        verb = "mauls"
        color = Colors.YELLOW
    elif damage < 40:
        verb = "decimates"
        color = Colors.RED
    else:
        verb = "OBLITERATES"
        color = Colors.BOLD + Colors.RED
        
    colored_verb = f"{color}{verb}{Colors.RESET}"
    
    src_str = f" with {source}" if source else ""
    dmg_str = f"{color}{damage}{Colors.RESET}"
    
    att_msg = f"You {colored_verb} {target_name}{src_str} for {dmg_str} damage."
    tgt_msg = f"{attacker_name} {colored_verb} you{src_str} for {dmg_str} damage."
    room_msg = f"{attacker_name} {colored_verb} {target_name}{src_str}."
    
    return att_msg, tgt_msg, room_msg