import logic.handlers.command_manager as command_manager
from utilities.colors import Colors
from logic.core.utils import display_utils
from logic.core import search

@command_manager.register("who", category="information")
def who(player, args):
    """List all online players."""
    player.send_line(f"\n{display_utils.render_header('Online Players', 60)}")
    
    sessions = getattr(player.game, 'sessions', [])
    if isinstance(sessions, dict): sessions = list(sessions.values())
        
    count = 0
    for session in sessions:
        if hasattr(session, 'player') and session.player:
            p = session.player
            status = f" {Colors.RED}(Fighting){Colors.RESET}" if p.state == "combat" else ""
            cls_name = p.active_class.replace('_', ' ').title() if p.active_class else "Wanderer"
            player.send_line(f" [{cls_name:<12}] {p.name}{status}")
            count += 1
    player.send_line(f"\n Total Players: {count}")

@command_manager.register("finger", category="information")
def finger(player, args):
    """Get details about a player."""
    if not args: return player.send_line("Finger whom?")
    target_name = args.lower()
    target = None
    
    sessions = getattr(player.game, 'sessions', [])
    if isinstance(sessions, dict): sessions = list(sessions.values())
    for s in sessions:
        if hasattr(s, 'player') and s.player and s.player.name.lower() == target_name:
            target = s.player; break
    
    if not target: return player.send_line(f"No player named '{args}' online.")
        
    player.send_line(f"\n{display_utils.render_header(target.name, 60)}")
    player.send_line(display_utils.render_labeled_value("Class", target.active_class.title() if target.active_class else "Wanderer"))
    player.send_line(display_utils.render_labeled_value("Kingdom", target.identity_tags[0].title() if target.identity_tags else "None"))
    
    loc = f"{target.room.name} ({target.room.zone_id})" if target.room else "Unknown"
    player.send_line(display_utils.render_labeled_value("Location", loc))
    if target.description: player.send_line(f" {Colors.WHITE}{target.description}{Colors.RESET}")

@command_manager.register("class", "classes", category="information")
def class_info(player, args):
    """Check class status and resonance progress."""
    from logic.engines.resonance_engine import ResonanceAuditor
    ResonanceAuditor.calculate_resonance(player)
    voltage = player.current_tags

    if args and args.lower() != 'all':
        candidates = search.find_matches(player.game.world.classes.values(), args.lower())
        if len(candidates) > 1:
            player.send_line(f"Multiple matches: {', '.join([c.name for c in candidates])}")
        elif len(candidates) == 1:
            cls = candidates[0]
            player.send_line(f"\n{display_utils.render_header(f'Class Dossier: {cls.name}', 60)}")
            player.send_line(f" Kingdom: {cls.kingdom.title()}")
            player.send_line(f" {cls.description}")
            
            recipe = getattr(cls, 'recipe', {})
            if recipe:
                reqs = []
                for tag, val in recipe.items():
                    have = voltage.get(tag, 0)
                    col = Colors.GREEN if have >= val else Colors.RED
                    reqs.append(f"{tag.title()}: {col}{have}/{val}{Colors.RESET}")
                player.send_line(f" Requirements: {', '.join(reqs)}")
        else: player.send_line(f"No class found matching '{args}'.")
        return

    # List Current + Resonances
    current_id = player.active_class or "wanderer"
    curr = player.game.world.classes.get(current_id)
    player.send_line(f"\n{display_utils.render_header('Class Identity', 60)}")
    player.send_line(f" Active: {Colors.GREEN}{curr.name if curr else 'Wanderer'}{Colors.RESET}")
    
    player.send_line(f"\n {Colors.BOLD}Class Resonance (Voltage){Colors.RESET}")
    all_cls = sorted(player.game.world.classes.values(), key=lambda x: x.name)
    for cls in all_cls:
        if cls.id in [current_id, "wanderer"]: continue
        reqs = getattr(cls, 'recipe', {})
        if not reqs: continue
        
        met = sum(1 for tag, val in reqs.items() if voltage.get(tag, 0) >= val)
        if met > 0 or args == 'all':
            req_strs = [f"{t}: {voltage.get(t,0)}/{v}" for t, v in reqs.items()]
            player.send_line(f" {Colors.CYAN}{cls.name:<15}{Colors.RESET} [{', '.join(req_strs)}]")

@command_manager.register("tags", category="information")
def list_tags(player, args):
    """List blessing tags and frequency."""
    tag_data = {}
    for b in player.game.world.blessings.values():
        for tag in b.identity_tags:
            if tag not in tag_data: tag_data[tag] = {'count': 0, 'sources': set()}
            tag_data[tag]['count'] += 1
            if b.deity_id: tag_data[tag]['sources'].add(b.deity_id)
            
    player.send_line(f"\n{display_utils.render_header('Tag Registry', 60)}")
    filter_str = args.lower() if args else None
    for tag in sorted(tag_data.keys()):
        if filter_str and filter_str not in tag: continue
        data = tag_data[tag]
        sources = ", ".join(sorted(list(data['sources']))) if data['sources'] else "None"
        player.send_line(f" {Colors.CYAN}{tag:<20}{Colors.RESET} Count: {data['count']:<3} Sources: {sources}")

@command_manager.register("motd", category="information")
def motd(player, args):
    """Show the Message of the Day."""
    try:
        with open('data/motd.txt', 'r') as f:
            player.send_line(f"\n{Colors.CYAN}{f.read()}{Colors.RESET}")
    except FileNotFoundError: player.send_line("No MOTD set.")
