import time
import asyncio
import logic.handlers.command_manager as command_manager
from logic.engines import blessings_engine
from logic.engines import magic_engine
from logic.core import effects
from logic import search
from utilities.colors import Colors
from utilities import telemetry
from logic.common import find_by_index
from logic.actions.registry import SKILL_HANDLERS as SKILL_REGISTRY
from logic.actions.skill_utils import _apply_damage
from logic.actions.base_executor import execute as handle_generic

# Ensure handlers are registered by importing them
from logic.actions.handlers import (
    combat_actions, 
    magic_actions, 
    status_actions, 
    utility, 
    world_actions,
    thievery_actions,
    engineering_actions,
    alchemy_actions
)

MIN_ACTION_DELAY = 0.15 # 150ms Hard Floor

def try_execute_skill(player, command_line):
    """
    Parses input to see if it matches an equipped skill (blessing).
    Syntax: <skill_name> [target/direction]
    Example: "kick goblin", "flask_toss north", "snipe"
    """
    parts = command_line.split()
    trigger = parts[0].lower()
    args = " ".join(parts[1:]) if len(parts) > 1 else ""
    
    # Fuzzy Resolution Logic
    # Priority:
    # 1. Exact Match (slug or name)
    # 2. Word Match (trigger is a distinct word in the name, e.g. "charge" in "mounted charge")
    # 3. Starts With (trigger is the start of the name)
    
    candidates = []
    
    for b_id in player.equipped_blessings:
        b = player.game.world.blessings.get(b_id)
        if not b: continue

        # Global Command Registration: Allow ANY equipped blessing to be triggered
        # (Removed 'is_skill' check)

        b_name = b.name.lower()
        b_slug = b_name.replace(" ", "_")
        
        # 1. Exact Match
        if b_slug == trigger or b_name == trigger:
            _execute_skill(player, b, args)
            return True
            
        # 2. Word Match
        # Split by space or underscore to find whole words
        name_parts = b_name.replace("_", " ").split()
        if trigger in name_parts:
            candidates.append((b, 2)) # High priority
            continue
            
        # 3. Starts With
        if b_slug.startswith(trigger):
            candidates.append((b, 1)) # Low priority
            continue

    if candidates:
        # Sort by priority (descending)
        candidates.sort(key=lambda x: x[1], reverse=True)
        _execute_skill(player, candidates[0][0], args)
        return True

    return False

def _execute_skill(player, skill, args):
    # 0. Hard Floor: Macro-Killer (Silently Drop)
    if hasattr(player, 'last_action_time') and time.time() < player.last_action_time + MIN_ACTION_DELAY:
        return

    # 0. Hard Gate: Stalled (Prevent Spam)
    if "stalled" in getattr(player, 'status_effects', {}):
        player.send_line(f"{Colors.RED}You are too exhausted to act!{Colors.RESET}")
        return

    # 1. Validation
    
    # Check Requirements (Stance, Mount, Terrain, etc.)
    valid_req, reason_req = blessings_engine.Auditor.check_requirements(skill, player, args=args)
    if not valid_req:
        if reason_req.startswith("BUFFERED|"):
            # Parse wait time from protocol string
            try:
                wait_time = float(reason_req.split("|")[1])
                async def _buffered_skill():
                    await asyncio.sleep(wait_time)
                    if player and player.game:
                        _execute_skill(player, skill, args)
                        
                        # [SNAPPY FEEDBACK] Refresh prompt after buffered skill
                        if player.room:
                            for p in player.room.players:
                                p.prompt_requested = True
                        else:
                            player.prompt_requested = True
                asyncio.create_task(_buffered_skill())
            except (IndexError, ValueError):
                pass
            return
        telemetry.log_event(player, "SKILL_EXECUTE", {"skill": skill.name, "args": args, "result": f"FAILED: {reason_req}"})
        player.send_line(reason_req)
        return

    # 1.5 Pacing Check (Actions per Round)
    can_pace, reason_pace = magic_engine.check_pacing(player, skill)
    if not can_pace:
        telemetry.log_event(player, "SKILL_EXECUTE", {"skill": skill.name, "args": args, "result": f"FAILED: {reason_pace}"})
        player.send_line(reason_pace)
        return

    # Update Action Time (Hard Floor)
    player.last_action_time = time.time()

    telemetry.log_event(player, "SKILL_EXECUTE", {"skill": skill.name, "args": args})

    # 2. Dispatch
    target = None
    handled = False

    # 0. Dispatch by ID or Action Key (Specific Override)
    action_key = getattr(skill, 'action', None)
    
    if (skill.id in SKILL_REGISTRY) or (action_key and action_key in SKILL_REGISTRY):
        key = skill.id if skill.id in SKILL_REGISTRY else action_key
        t_ent, stop = SKILL_REGISTRY[key](player, skill, args)
        if stop: return
        if t_ent: target = t_ent; handled = True

    if not handled:
        # Optimized Dispatch: Check tags against the registry
        # This avoids creating 20+ lambda functions every time a skill is used.
        for tag, handler_func in SKILL_REGISTRY.items():
            if tag in skill.identity_tags:
                # Special case for alchemy which needed two tags in the old code
                if tag == "alchemy" and "ranged" not in skill.identity_tags:
                    continue
                    
                t_ent, stop = handler_func(player, skill, args)
                if stop:
                    return
                if t_ent:
                    target = t_ent
                    handled = True
                
                # If the specific handler already dealt with resources, stop now.
                if stop:
                    return

                break

    if not handled:
        handle_generic(player, skill, args)
        
    # Mark that the skill user needs a prompt update
    player.prompt_requested = True

def register_modules():
    """Sharded module registration via module_loader."""
    from logic.commands import module_loader
    module_loader.register_all_modules()
