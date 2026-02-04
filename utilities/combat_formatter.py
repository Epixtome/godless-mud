from utilities.colors import Colors

VERB_PAIRS = {
    "misses": "miss",
    "scratches": "scratch",
    "hits": "hit",
    "mauls": "maul",
    "decimates": "decimate",
    "OBLITERATES": "OBLITERATE"
}

def format_damage(attacker_name, target_name, damage, source=None):
    """
    Returns (attacker_msg, target_msg, room_msg) with colored verbs.
    """
    verb_3rd = "hits"
    color = Colors.WHITE
    
    if damage <= 0:
        verb_3rd = "misses"
    elif damage < 5:
        verb_3rd = "scratches"
    elif damage < 10:
        verb_3rd = "hits"
    elif damage < 20:
        verb_3rd = "mauls"
        color = Colors.YELLOW
    elif damage < 40:
        verb_3rd = "decimates"
        color = Colors.RED
    else:
        verb_3rd = "OBLITERATES"
        color = Colors.BOLD + Colors.RED
        
    verb_2nd = VERB_PAIRS.get(verb_3rd, verb_3rd) # You hit/maul
    
    colored_verb_3rd = f"{color}{verb_3rd}{Colors.RESET}"
    colored_verb_2nd = f"{color}{verb_2nd}{Colors.RESET}"
    
    src_str = f" with {source}" if source else ""
    dmg_str = f"{color}{damage}{Colors.RESET}"
    
    att_msg = f"You {colored_verb_2nd} {target_name}{src_str} for {dmg_str} damage."
    tgt_msg = f"{attacker_name} {colored_verb_3rd} you{src_str} for {dmg_str} damage."
    room_msg = f"{attacker_name} {colored_verb_3rd} {target_name}{src_str} for {dmg_str} damage."
    
    return att_msg, tgt_msg, room_msg