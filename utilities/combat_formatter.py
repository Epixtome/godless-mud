from utilities.colors import Colors
from logic.core import combat

def format_combat_messages(attacker, target, damage, blessing=None, is_god=False):
    """
    Generates tailored combat strings for attacker, target, and room.
    """
    damage_percent = 0.0
    if hasattr(target, 'max_hp') and target.max_hp > 0:
        damage_percent = damage / target.max_hp
    
    verb = combat.get_attack_verb(damage_percent)
    verb_3rd = verb + "es" if verb.endswith("sh") or verb.endswith("ch") else verb + "s"

    if is_god:
        tgt_msg = f"{Colors.CYAN}You ignore the damage because you are a GOD.{Colors.RESET}"
        att_msg = f"{Colors.YELLOW}Your attack strikes {target.name}, but they seem unharmed.{Colors.RESET}"
        room_msg = f"{Colors.YELLOW}{attacker.name}'s attack strikes {target.name}, but it has no effect.{Colors.RESET}"
        return att_msg, tgt_msg, room_msg

    if blessing:
        att_msg = f"{Colors.GREEN}You {verb} {target.name} with {blessing.name} for {Colors.YELLOW}{damage}{Colors.GREEN} damage.{Colors.RESET}"
        tgt_msg = f"{Colors.YELLOW}{attacker.name} {verb_3rd} you with {blessing.name} for {Colors.RED}{damage}{Colors.YELLOW} damage.{Colors.RESET}"
        room_msg = f"{Colors.YELLOW}{attacker.name} {verb_3rd} {target.name} with {blessing.name} for {Colors.RED}{damage}{Colors.YELLOW} damage.{Colors.RESET}"
    else:
        att_msg = f"{Colors.GREEN}You {verb} {target.name} for {Colors.YELLOW}{damage}{Colors.GREEN} damage.{Colors.RESET}"
        tgt_msg = f"{Colors.YELLOW}{attacker.name} {verb_3rd} you for {Colors.RED}{damage}{Colors.YELLOW} damage.{Colors.RESET}"
        room_msg = f"{Colors.YELLOW}{attacker.name} {verb_3rd} {target.name} for {Colors.RED}{damage}{Colors.YELLOW} damage.{Colors.RESET}"

    return att_msg, tgt_msg, room_msg

def broadcast_combat_results(room, attacker, target, att_msg, tgt_msg, room_msg):
    """Dispatches messages to the appropriate parties in the room."""
    if hasattr(attacker, 'send_line'):
        attacker.send_line(att_msg)
    
    if hasattr(target, 'send_line'):
        target.send_line(tgt_msg)

    for p in getattr(room, 'players', []):
        if p != attacker and p != target:
            p.send_line(room_msg)