"""
logic/core/systems/battle_logger.py
Live Combat Recording System.
Captures in-game battles and generates Markdown reports for analysis.
"""
import logging
import datetime
import os
import re
from collections import defaultdict
from logic.core import event_engine

logger = logging.getLogger("GodlessMUD")

# In-memory storage for active encounters
# Key: room_id, Value: List of event dictionaries
_ACTIVE_ENCOUNTERS = {}
_LAST_ACTIVITY = {} # Tracks the last tick an encounter was active

def _ensure_dir():
    if not os.path.exists("logs/battles"):
        os.makedirs("logs/battles")

def _strip_ansi(text):
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

def on_combat_event(ctx, event_type):
    """Unified listener for all combat hooks."""
    room = ctx.get('room')
    if not room:
        # Try to resolve room from entity
        entity = ctx.get('attacker') or ctx.get('target') or ctx.get('entity') or ctx.get('victim')
        room = getattr(entity, 'room', None)
    
    if not room:
        return

    room_id = getattr(room, 'id', 'unknown')
    
    if room_id not in _ACTIVE_ENCOUNTERS:
        _ACTIVE_ENCOUNTERS[room_id] = []
        _ACTIVE_ENCOUNTERS[room_id].append({
            'time': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'type': 'ENCOUNTER_START',
            'room': room_id,
            'terrain': getattr(room, 'terrain', 'normal'),
            'weather': getattr(room, 'weather', 'clear')
        })
    
    _LAST_ACTIVITY[room_id] = datetime.datetime.now()
    
    # Log the event
    timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
    entry = {'time': timestamp, 'type': event_type, 'data': {}}
    
    if event_type == "on_combat_hit":
        entry['data'] = {
            'attacker': getattr(ctx.get('attacker'), 'name', 'Unknown'),
            'target': getattr(ctx.get('target'), 'name', 'Unknown'),
            'damage': ctx.get('damage', 0),
            'blessing': getattr(ctx.get('blessing'), 'name', 'Auto-Attack') if ctx.get('blessing') else 'Auto-Attack'
        }
    elif event_type == "on_skill_use":
        entry['data'] = {
            'attacker': getattr(ctx.get('attacker'), 'name', 'Unknown'),
            'target': getattr(ctx.get('target'), 'name', 'Unknown'),
            'blessing': getattr(ctx.get('blessing'), 'name', 'Unknown') if ctx.get('blessing') else 'Unknown'
        }
    elif event_type == "on_combat_miss":
        entry['data'] = {
            'attacker': getattr(ctx.get('attacker'), 'name', 'Unknown'),
            'target': getattr(ctx.get('target'), 'name', 'Unknown'),
            'reason': ctx.get('reason', 'miss'),
            'blessing': getattr(ctx.get('blessing'), 'name', 'Auto-Attack') if ctx.get('blessing') else 'Auto-Attack'
        }
    elif event_type == "on_flee":
        entry['data'] = {
            'entity': getattr(ctx.get('entity'), 'name', 'Unknown'),
            'direction': ctx.get('direction', 'away')
        }
    elif event_type == "on_status_applied":
        entry['data'] = {
            'target': getattr(ctx.get('target'), 'name', 'Unknown'),
            'status': ctx.get('status_id', 'unknown'),
            'duration': ctx.get('duration', 0)
        }
    elif event_type == "on_death":
        entry['data'] = {
            'victim': getattr(ctx.get('victim'), 'name', 'Unknown'),
            'killer': getattr(ctx.get('killer'), 'name', 'Environment') if ctx.get('killer') else 'Environment'
        }
    elif event_type == "on_favor_gain":
        entry['data'] = {
            'player': getattr(ctx.get('player'), 'name', 'Unknown'),
            'deity': getattr(ctx.get('deity'), 'name', str(ctx.get('deity'))) if ctx.get('deity') else 'Unknown',
            'amount': ctx.get('amount', 0)
        }
    elif event_type == "on_status_removed":
        entry['data'] = {
            'target': getattr(ctx.get('target'), 'name', 'Unknown'),
            'status': ctx.get('status_id', 'unknown')
        }

    _ACTIVE_ENCOUNTERS[room_id].append(entry)

def flush_inactive_encounters(game):
    """
    Called periodically (e.g., via heartbeat or dedicated tick).
    Saves encounters that have seen no activity for X seconds.
    """
    now = datetime.datetime.now()
    to_flush = []
    
    for rid, last_time in _LAST_ACTIVITY.items():
        if (now - last_time).total_seconds() > 20: # Extended to 20s to allow for fleeing/returning
            to_flush.append(rid)
            
    for rid in to_flush:
        _save_report(rid)
        del _ACTIVE_ENCOUNTERS[rid]
        del _LAST_ACTIVITY[rid]

def _save_report(room_id):
    _ensure_dir()
    events = _ACTIVE_ENCOUNTERS.get(room_id, [])
    if not events: return
    
    start_info = events[0]
    # Sanitize room_id for filename
    safe_rid = _strip_ansi(room_id).replace(".", "_")
    filename = f"logs/battles/battle_{safe_rid}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# Combat Report: {room_id}\n")
        f.write(f"**Date:** {start_info['time']}\n")
        f.write(f"**Environment:** {start_info['terrain']} | {start_info['weather']}\n\n")
        f.write("## Timeline\n\n")
        
        for e in events[1:]:
            ts = e['time']
            etype = e['type']
            d = e['data']
            
            if etype == "on_combat_hit":
                f.write(f"[{ts}] **{d['attacker']}** hit **{d['target']}** for **{d['damage']}** DMG using `{d['blessing']}`.\n")
            elif etype == "on_combat_miss":
                f.write(f"[{ts}] **{d['attacker']}**'s `{d['blessing']}` was **{d['reason']}ed** by **{d['target']}**.\n")
            elif etype == "on_skill_use":
                f.write(f"[{ts}] **{d['attacker']}** activated `{d['blessing']}` targeting **{d['target']}**.\n")
            elif etype == "on_flee":
                f.write(f"[{ts}] 🏃 **{d['entity']}** fled the room to the **{d['direction']}**.\n")
            elif etype == "on_status_applied":
                f.write(f"[{ts}] ✨ **{d['target']}** gained status: `{d['status']}` ({d['duration']}s).\n")
            elif etype == "on_status_removed":
                f.write(f"[{ts}] 🍃 **{d['target']}**'s status expired: `{d['status']}`.\n")
            elif etype == "on_favor_gain":
                f.write(f"[{ts}] 🙏 **{d['player']}** gained **{d['amount']}** Favor with **{d['deity']}**.\n")
            elif etype == "on_death":
                f.write(f"[{ts}] 💀 **{d['victim']}** was slain by **{d['killer']}**.\n")
                
    logger.info(f"Battle report saved: {filename}")

def initialize():
    """Subscribes to combat events."""
    event_engine.subscribe("on_combat_hit", lambda ctx: on_combat_event(ctx, "on_combat_hit"))
    event_engine.subscribe("on_skill_use", lambda ctx: on_combat_event(ctx, "on_skill_use"))
    event_engine.subscribe("on_combat_miss", lambda ctx: on_combat_event(ctx, "on_combat_miss"))
    event_engine.subscribe("on_flee", lambda ctx: on_combat_event(ctx, "on_flee"))
    event_engine.subscribe("on_status_applied", lambda ctx: on_combat_event(ctx, "on_status_applied"))
    event_engine.subscribe("on_status_removed", lambda ctx: on_combat_event(ctx, "on_status_removed"))
    event_engine.subscribe("on_favor_gain", lambda ctx: on_combat_event(ctx, "on_favor_gain"))
    event_engine.subscribe("on_death", lambda ctx: on_combat_event(ctx, "on_death"))
    logger.info("Battle Logger initialized.")
