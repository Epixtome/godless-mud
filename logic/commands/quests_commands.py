import logic.handlers.command_manager as command_manager
from logic.core import search
from logic.core import quest_engine
from utilities.colors import Colors

@command_manager.register("quest", category="social")
def quest_command(player, args):
    """Interact with quests. Usage: quest <log|list|accept|complete>"""
    if not args:
        player.send_line("Usage: quest <log | list [target] | accept <id> [target] | complete <id> [target]>")
        return

    parts = args.split()
    sub_cmd = parts[0].lower()
    cmd_args = parts[1:]

    if sub_cmd == "log":
        _show_log(player)
    elif sub_cmd == "list":
        _list_quests(player, " ".join(cmd_args))
    elif sub_cmd == "accept":
        _accept_quest(player, cmd_args)
    elif sub_cmd == "complete":
        _complete_quest(player, cmd_args)
    else:
        player.send_line("Unknown quest command. Use: log, list, accept, complete.")

def _find_quest_giver(player, target_name):
    """Finds a quest-giving NPC in the room."""
    if not target_name:
        # Find any quest giver in the room
        for npc in player.room.monsters:
            if "quest_giver" in npc.tags:
                return npc
        return None
    else:
        return search.find_living(player.room, target_name)

def _list_quests(player, target_name):
    npc = _find_quest_giver(player, target_name)
    if not npc:
        player.send_line("No one here has any quests for you.")
        return

    available_quests = []
    for quest_id in npc.quests:
        quest = player.game.world.quests.get(quest_id)
        if quest:
            if quest_id in player.active_quests:
                # Optional: Show active quests with a marker?
                pass
            elif quest_id in player.completed_quests:
                pass
            else:
                available_quests.append(quest)

    if not available_quests:
        player.send_line(f"{npc.name} has no new quests for you at this time.")
        return

    player.send_line(f"--- Quests from {npc.name} ---")
    for quest in available_quests:
        player.send_line(f"[{quest.id}] {Colors.YELLOW}{quest.name}{Colors.RESET}")
        player.send_line(f"  {quest.giver_text}")

def _accept_quest(player, cmd_args):
    if not cmd_args:
        player.send_line("Accept which quest from whom?")
        return
    
    # Parse args: <quest_name_or_id> [from] <npc_name>
    # This is tricky because quest names have spaces.
    # Simplified approach: Assume last word is NPC name if > 1 word? No, NPC names have spaces too.
    # Let's stick to: First arg is ID/Name, rest is NPC.
    quest_search = cmd_args[0].lower()
    target_name = " ".join(cmd_args[1:])

    npc = _find_quest_giver(player, target_name)
    if not npc:
        player.send_line("You don't see them here.")
        return

    # Find quest in NPC's list by ID or Name
    quest = None
    for q_id in npc.quests:
        q = player.game.world.quests.get(q_id)
        if q and (q.id.lower() == quest_search or quest_search in q.name.lower()):
            quest = q
            break
            
    if not quest:
        player.send_line("That quest is not available from them.")
        return

    success, msg = quest_engine.accept_quest(player, quest)
    player.send_line(msg)

def _show_log(player):
    if not player.active_quests:
        player.send_line("You have no active quests.")
        return

    player.send_line("--- Quest Log ---")
    for quest_id in player.active_quests:
        quest = player.game.world.quests.get(quest_id)
        if quest:
            player.send_line(f"[{quest.id}] {Colors.YELLOW}{quest.name}{Colors.RESET}")
            player.send_line(f"  - {quest.log_text}")

def _complete_quest(player, cmd_args):
    if not cmd_args:
        player.send_line("Complete which quest for whom?")
        return
    quest_id = cmd_args[0]
    target_name = " ".join(cmd_args[1:])

    if quest_id not in player.active_quests:
        player.send_line("You do not have that quest.")
        return

    npc = _find_quest_giver(player, target_name)
    if not npc or quest_id not in npc.quests:
        player.send_line("You can't turn that quest in here.")
        return

    quest = player.game.world.quests.get(quest_id)
    if not quest: return

    can_complete, msg = quest_engine.check_completion(player, quest)
    if not can_complete:
        player.send_line(msg)
        return
        
    msg = quest_engine.complete_quest(player, quest)
    player.send_line(msg)
