from utilities.colors import Colors

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
    """Verifies if all objectives are met."""
    for obj in quest.objectives:
        obj_type = obj.get('type')
        if obj_type == 'item':
            found_item = next((item for item in player.inventory if hasattr(item, 'prototype_id') and item.prototype_id == obj['id']), None)
            if not found_item:
                return False, f"You don't have the required item: {obj['id']}"
        elif obj_type == 'kill':
            progress = player.active_quests.get(quest.id, {})
            killed_count = progress.get(obj['id'], 0)
            if killed_count < obj['count']:
                return False, f"You have not yet defeated enough {obj['id']}s. ({killed_count}/{obj['count']})"
    return True, "OK"

def complete_quest(player, quest):
    """Completes the quest, consumes items, and grants rewards."""
    # Consume items
    for obj in quest.objectives:
        if obj.get('type') == 'item':
            found_item = next((item for item in player.inventory if hasattr(item, 'prototype_id') and item.prototype_id == obj['id']), None)
            if found_item:
                player.inventory.remove(found_item)
    
    # Grant rewards
    for reward in quest.rewards:
        if reward['type'] == 'gold':
            player.gold += reward['amount']
            player.send_line(f"You receive {reward['amount']} gold.")
            
    del player.active_quests[quest.id]
    player.completed_quests.append(quest.id)
    return f"You have completed: {Colors.YELLOW}{quest.name}{Colors.RESET}!"

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