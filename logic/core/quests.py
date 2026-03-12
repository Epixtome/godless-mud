from utilities.colors import Colors
from logic.core import event_engine

def register_events():
    """Hooks the quest system into the global event loop."""
    event_engine.subscribe("after_move", on_player_move)
    event_engine.subscribe("on_mob_death", on_mob_killed)

def on_player_move(ctx):
    player = ctx.get('player')
    room = ctx.get('new_room')
    if player and room:
        update_visit_progress(player, room)

def on_mob_killed(ctx):
    player = ctx.get('killer')
    mob = ctx.get('mob')
    if player and mob:
        update_kill_progress(player, mob.prototype_id)

def can_accept(player, quest):
    """Checks if a player can accept a quest."""
    if quest.id in player.active_quests:
        return False, "You have already accepted that quest."
    if quest.id in player.completed_quests:
        return False, "You have already completed that quest."
    return True, "OK"

def accept_quest(player, quest):
    """Accepts a quest and initializes objectives."""
    ok, msg = can_accept(player, quest)
    if not ok:
        return False, msg
    
    player.active_quests[quest.id] = {}
    # Initialize counters for kill objectives
    for obj in quest.objectives:
        if obj.get('type') == 'kill':
            player.active_quests[quest.id][obj['id']] = 0
            
    return True, f"You have accepted the quest: {Colors.YELLOW}{quest.name}{Colors.RESET}"

def check_completion(player, quest):
    """Verifies if all objectives are met via data-driven validation."""
    for obj in quest.objectives:
        obj_type = obj.get('type')
        if obj_type == 'item':
            from logic.core import search
            found_item = search.search_list(player.inventory, obj['id'])
            if not found_item:
                return False, f"You don't have the required item: {obj['id']}"
        elif obj_type == 'kill':
            progress = player.active_quests.get(quest.id, {})
            killed_count = progress.get(obj['id'], 0)
            if killed_count < obj['count']:
                return False, f"You have not yet defeated enough {obj['id']}s. ({killed_count}/{obj['count']})"
        elif obj_type == 'visit':
            progress = player.active_quests.get(quest.id, {})
            if not progress.get(obj['id']):
                return False, f"You have not yet reached the required location: {quest.log_text}"
        elif obj_type == 'reputation':
            if player.reputation < obj.get('value', 0):
                return False, f"Your reputation ({player.reputation}) is too low. Need {obj['value']}."
                
    return True, "OK"

def complete_quest(player, quest):
    """Completes the quest, consumes items, and grants sharded rewards."""
    # Consume items
    for obj in quest.objectives:
        if obj.get('type') == 'item':
            from logic.core import search
            found_item = search.search_list(player.inventory, obj['id'])
            if found_item:
                player.inventory.remove(found_item)
    
    # Grant rewards
    for reward in quest.rewards:
        r_type = reward.get('type')
        if r_type == 'gold':
            player.gold += reward['amount']
            player.send_line(f"You receive {Colors.YELLOW}{reward['amount']} gold{Colors.RESET}.")
        elif r_type == 'favor':
            deity = reward.get('deity', 'any')
            if deity == 'any':
                # Grant to all known deities equally or pick one? 
                # For now, let's just grant to current class deity if exists
                pass # TODO: Implement complex favor rewards
            else:
                player.favor[deity] = player.favor.get(deity, 0) + reward['amount']
                player.send_line(f"You receive {Colors.CYAN}{reward['amount']} favor{Colors.RESET} with {deity.capitalize()}.")
            
    del player.active_quests[quest.id]
    player.completed_quests.append(quest.id)
    
    # TRIGGER: Quest Completed event
    from logic.core import event_engine
    event_engine.dispatch("quest_completed", {'player': player, 'quest': quest})
    
    return f"You have completed: {Colors.YELLOW}{quest.name}{Colors.RESET}!"

def update_visit_progress(player, room):
    """Checks if entering a room satisfies a 'visit' objective."""
    if not player.active_quests: return
    
    for quest_id, progress in player.active_quests.items():
        quest = player.game.world.quests.get(quest_id)
        if not quest: continue
        for obj in quest.objectives:
            if obj.get('type') == 'visit' and not progress.get(obj['id']):
                target_coords = obj.get('coords')
                if target_coords and room.coords == tuple(target_coords):
                    progress[obj['id']] = True
                    player.send_line(f"\n{Colors.GREEN}[Quest Update: {quest.name}]{Colors.RESET}")
                    player.send_line(f"{Colors.WHITE}Location reached: {obj['id']}{Colors.RESET}")

def update_kill_progress(player, killed_mob_id):
    """Updates kill objectives for active quests."""
    if not player.active_quests or not killed_mob_id:
        return

    for quest_id, progress in player.active_quests.items():
        quest = player.game.world.quests.get(quest_id)
        if not quest: continue
        for obj in quest.objectives:
            if obj.get('type') == 'kill' and obj.get('id') == killed_mob_id:
                # Ensure counter exists (for legacy saves or data updates)
                if obj['id'] not in progress:
                    progress[obj['id']] = 0
                    
                if progress[obj['id']] < obj['count']:
                    progress[obj['id']] += 1
                    player.send_line(f"[{quest.name}] {progress[obj['id']]}/{obj['count']} {killed_mob_id} killed.")
