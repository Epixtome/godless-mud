"""
logic/core/effects.py
The Effects Service. Manages application, removal, and processing of status effects.
"""
import logging
import json
import os
from utilities.colors import Colors
from utilities import telemetry
from logic.core import event_engine
from logic.core.systems.status.definitions import (
    STATUS_MAP, CRITICAL_STATES, HARD_DEBUFFS, SOFT_DEBUFFS, CORE_STATUS_DEFINITIONS
)

logger = logging.getLogger("GodlessMUD")

def apply_effect(target, effect_id, duration, verbose=True, log_event=True):
    """Applies a status effect to the target, respecting hierarchy rules."""
    if not target: return
    
    # Normalize ID for case-insensitivity consistency across engines
    effect_id = str(effect_id).lower().strip()
    
    if effect_id in STATUS_MAP: effect_id = STATUS_MAP[effect_id]

    # Immunity Checks
    if hasattr(target, 'status_effects'):
        game = getattr(target, 'game', None)
        for active_id in target.status_effects:
            active_def = get_effect_definition(active_id, game)
            if isinstance(active_def, dict):
                meta = active_def.get('metadata', {})
                if isinstance(meta, dict):
                    immune_list = meta.get('immune_to', [])
                    if isinstance(immune_list, list) and effect_id in immune_list:
                        if hasattr(target, 'send_line'):
                            target.send_line(f"{Colors.YELLOW}[!] You are immune to that effect!{Colors.RESET}")
                        return

    # Critical State Exclusivity
    if effect_id in CRITICAL_STATES:
        to_remove = [eff for eff in target.status_effects if eff in CRITICAL_STATES and eff != effect_id]
        for eff in to_remove: remove_effect(target, eff, verbose=False)

    # Persistence Tracking
    if not hasattr(target, 'status_effects'): target.status_effects = {}
    if not hasattr(target, 'status_effect_starts'): target.status_effect_starts = {}
    
    game = getattr(target, 'game', None)
    current_tick = game.tick_count if game else 0
    target.status_effect_starts[effect_id] = current_tick
    target.status_effects[effect_id] = current_tick + duration if game else duration
    
    if hasattr(target, "mark_tags_dirty"): target.mark_tags_dirty()
    if log_event: telemetry.log_status_change(target, effect_id, "applied", duration)

def remove_effect(target, effect_id, verbose=True):
    """Removes a status effect."""
    effect_id = str(effect_id).lower().strip()
    if effect_id == "prone":
        game = getattr(target, 'game', None)
        current_tick = game.tick_count if game else 0
        if getattr(target, 'status_effect_starts', {}).get(effect_id, -1) == current_tick:
            if verbose and hasattr(target, 'send_line'):
                target.send_line(f"{Colors.RED}You are too off-balance to recover yet!{Colors.RESET}")
            return False

    if effect_id in getattr(target, 'status_effects', {}):
        del target.status_effects[effect_id]
        if hasattr(target, "mark_tags_dirty"): target.mark_tags_dirty()
        telemetry.log_status_change(target, effect_id, "removed")
        if verbose and hasattr(target, 'send_line') and effect_id != "panting":
            target.send_line(f"{Colors.CYAN}You are no longer {effect_id.replace('_', ' ')}.{Colors.RESET}")
        event_engine.dispatch("on_status_removed", {"player": target, "status_id": effect_id})
        return True
    return False

def clear_state(target):
    """Purges all status effects and reset states (Use for death/reset)."""
    if not hasattr(target, 'status_effects'): return
    
    # Copy keys to avoid mutation during iteration
    for eid in list(target.status_effects.keys()):
        remove_effect(target, eid, verbose=False)
        
    if hasattr(target, 'status_effect_starts'):
        target.status_effect_starts.clear()
        
    # [V5.1] Clear skill buffers
    if hasattr(target, 'pending_skill'):
        target.pending_skill = None

def has_effect(target, effect_id):
    """Checks if target has a specific effect."""
    return effect_id in getattr(target, 'status_effects', {})

def process_effects(game):
    """Called by heartbeat to expire effects."""
    for entity in list(game.players.values()): _process_entity_effects(game, entity)
    for room in game.world.rooms.values():
        _process_entity_effects(game, room) # Room-wide persistence effects
        for entity in list(room.monsters):
            if not getattr(entity, 'pending_death', False):
                _process_entity_effects(game, entity)

def _process_entity_effects(game, entity):
    if hasattr(entity, 'pending_skill') and entity.pending_skill:
        # Buffered Skill Logic
        ps = entity.pending_skill
        if game.tick_count >= getattr(entity, 'cooldowns', {}).get(ps['skill'].id, 0):
            del entity.pending_skill
            from logic.commands import skill_commands
            if hasattr(entity, 'send_line'): entity.send_line(f"{Colors.GREEN}Unleashing: {ps['skill'].name}{Colors.RESET}")
            skill_commands._execute_skill(entity, ps['skill'], ps['args'])

    if not getattr(entity, 'status_effects', None): return

    expired = []
    for eid, expiry in entity.status_effects.items():
        if expiry is not None and game.tick_count >= expiry:
            expired.append(eid)
            continue
        ctx = {'game': game, 'entity': entity, 'effect_id': eid, 'expire_now': False}
        event_engine.dispatch("effect_tick", ctx)
        if ctx['expire_now']: expired.append(eid)

    for eid in expired: remove_effect(entity, eid)

def get_effect_definition(effect_id, game):
    """Single Source of Truth for effect data."""
    if effect_id in CORE_STATUS_DEFINITIONS: return CORE_STATUS_DEFINITIONS[effect_id]
    if game and (db := getattr(game.world, 'status_effects', None)):
        if (defn := db.get(effect_id)): return defn
        path = f"data/status_effects/{effect_id}.json"
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    data = json.load(f)
                    game.world.status_effects[effect_id] = data
                    return data
            except: pass
    return None

def is_action_blocked(player, cmd_name):
    """Standardized action blocking via logic shard."""
    from logic.core.systems.status import validation
    return validation.is_action_blocked(player, cmd_name, get_effect_definition)

def get_status_help(keyword, game):
    """Metadata-rich help for status effects."""
    keyword = keyword.lower().strip()
    defn = get_effect_definition(keyword, game)
    if not defn:
        for k, v in CORE_STATUS_DEFINITIONS.items():
            name = v.get('name', '')
            if isinstance(name, str) and name.lower() == keyword: 
                defn = v
                break

    if defn:
        name = defn.get('name', keyword.title())
        body = defn.get('description', "No info available.")
        extras = []
        if (blocks := defn.get('blocks', [])): extras.append(f"Blocks: {', '.join(blocks).title()}")
        if (mods := defn.get('modifiers')):
            if isinstance(mods, dict):
                ml = [f"{str(k).replace('_', ' ').title()}: {v}" for k, v in mods.items()]
                extras.append(f"Modifiers: {', '.join(ml)}")
        if extras: body += "\n\n" + "\n".join(extras)
        return {"keywords": [keyword, name.lower()], "title": f"Status: {name}", "body": body, "category": "status"}
    return None
