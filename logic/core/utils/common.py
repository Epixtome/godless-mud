from utilities.colors import Colors

def get_reverse_direction(direction):
    mapping = {
        'north': 'south', 'south': 'north',
        'east': 'west', 'west': 'east',
        'up': 'down', 'down': 'up',
        'n': 's', 's': 'n',
        'e': 'w', 'w': 'e',
        'u': 'd', 'd': 'u'
    }
    return mapping.get(direction)

def find_by_index(objects, query):
    parts = query.split('.', 1)
    if len(parts) == 2 and parts[0].isdigit():
        index = int(parts[0])
        search_name = parts[1].lower()
    else:
        index = 1
        search_name = query.lower()

    count = 0
    for obj in objects:
        if search_name in obj.name.lower():
            count += 1
            if count == index:
                return obj
    return None

def format_blessings_by_tier_and_tag(blessings, relevant_tags):
    lines = []
    organized = {1: {}, 2: {}, 3: {}, 4: {}}
    
    sorted_blessings = sorted(blessings, key=lambda x: x.name)
    
    for b in sorted_blessings:
        sig_tags = sorted([t for t in b.identity_tags if t in relevant_tags])
        if not sig_tags:
            continue
            
        sig = tuple(sig_tags)
        
        if sig not in organized[b.tier]:
            organized[b.tier][sig] = []
        organized[b.tier][sig].append(b.name)

    for tier in range(1, 5):
        if organized[tier]:
            lines.append(f"  {Colors.CYAN}Tier {tier}{Colors.RESET}")
            sorted_sigs = sorted(organized[tier].keys(), key=lambda s: (len(s), s))
            
            for sig in sorted_sigs:
                tag_header = f"[{', '.join(sig)}]"
                lines.append(f"    {Colors.YELLOW}{tag_header}{Colors.RESET}")
                names = ", ".join(organized[tier][sig])
                lines.append(f"      {names}")
    
    return lines

def find_player_online(game, name):
    if not name: return None
    target_name = name.lower()
    for p in game.players.values():
        if p.name.lower() == target_name:
            return p
    return None

def _get_target(player, args, target=None, fail_msg="Use skill on whom?"):
    if target:
        return target
        
    if args:
        candidates = player.room.monsters + player.room.players
        found = find_by_index(candidates, args)
        if not found:
            player.send_line("You don't see them here.")
            return None
        return found
        
    if getattr(player, 'fighting', None):
        target = player.fighting
        is_alive = target.hp > 0
        is_here = (target in player.room.monsters) or (target in player.room.players)
        
        if not is_alive or not is_here:
            player.fighting = None
            if hasattr(player, 'state') and player.state == 'combat':
                player.state = 'normal'
            player.send_line("Your target is no longer here.")
            return None
            
        return target
        
    player.send_line(fail_msg)
    return None
