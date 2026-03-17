import logging
from logging.handlers import RotatingFileHandler
import json
import time
import datetime
import os
from utilities.colors import Colors

# Ensure logs directory exists
# Ensure directory structure
if not os.path.exists("logs/archives"):
    os.makedirs("logs/archives")

def rotate_session_logs():
    """
    Archives logs from the previous session into a dated folder.
    """
    files_to_archive = [f for f in os.listdir("logs") if f.endswith((".jsonl", ".log", ".md"))]
    if not files_to_archive:
        return

    # Use the modification time of the most recent log as the session end time
    latest_mod = 0.0
    for f in files_to_archive:
        f_path = os.path.join("logs", f)
        latest_mod = max(latest_mod, os.path.getmtime(f_path))
    
    session_ts = datetime.datetime.fromtimestamp(latest_mod).strftime("%Y%m%d_%H%M%S")
    archive_dir = os.path.join("logs", "archives", f"session_{session_ts}")
    
    if not os.path.exists(archive_dir):
        os.makedirs(archive_dir)
        for f in files_to_archive:
            try:
                os.rename(os.path.join("logs", f), os.path.join(archive_dir, f))
            except Exception:
                pass

# Prune old sessions before starting fresh
rotate_session_logs()

# Configure Telemetry Loggers
telemetry_logger = logging.getLogger("telemetry")
telemetry_logger.setLevel(logging.INFO)
telemetry_logger.propagate = False 

# Dedicated Construction Logger for AI retrieval
construction_logger = logging.getLogger("construction")
construction_logger.setLevel(logging.INFO)
construction_logger.propagate = False

bug_logger = logging.getLogger("bugs")
bug_logger.setLevel(logging.INFO)
bug_logger.propagate = False

marker_logger = logging.getLogger("markers")
marker_logger.setLevel(logging.INFO)
marker_logger.propagate = False

if not telemetry_logger.handlers:
    _handler = logging.FileHandler("logs/telemetry.jsonl", encoding='utf-8')
    _formatter = logging.Formatter('%(message)s')
    _handler.setFormatter(_formatter)
    telemetry_logger.addHandler(_handler)

if not construction_logger.handlers:
    _c_handler = logging.FileHandler("logs/construction.jsonl", encoding='utf-8')
    _c_formatter = logging.Formatter('%(message)s')
    _c_handler.setFormatter(_c_formatter)
    construction_logger.addHandler(_c_handler)

if not bug_logger.handlers:
    _b_handler = logging.FileHandler("logs/bugs.jsonl", encoding='utf-8')
    _b_formatter = logging.Formatter('%(message)s')
    _b_handler.setFormatter(_b_formatter)
    bug_logger.addHandler(_b_handler)

if not marker_logger.handlers:
    _m_handler = logging.FileHandler("logs/markers.jsonl", encoding='utf-8')
    _m_formatter = logging.Formatter('%(message)s')
    _m_handler.setFormatter(_m_formatter)
    marker_logger.addHandler(_m_handler)

VERBOSE_CONSOLE = False 

def _print_console_mirror(entity, event_type, data, timestamp, room_id):
    """Formats and prints telemetry events to the console."""
    # Silence High-Frequency Noise
    if event_type == "STATUS_CHANGE":
        eff = str(data.get('effect_id', '')).lower()
        # Skip weather/terrain spam in console
        if eff in ["wet", "cold", "hot", "dry"]:
            return

    if VERBOSE_CONSOLE:
        print(json.dumps({"time": timestamp, "entity": entity.name, "room_id": room_id, "type": event_type, "data": data}))
        return

    header = f"{Colors.WHITE}[{timestamp}] | [{entity.name}] | [{room_id}] |{Colors.RESET}"

    if event_type == "COMBAT_DETAIL":
        target = data.get('target', 'Unknown')
        dmg = data.get('final', 0)
        tags = data.get('tags', [])
        tag_str = ", ".join(tags) if tags else "none"
        skill_name = data.get('source', "Auto-Attack")
        print(f"{header} {Colors.RED}SKILL: {skill_name} -> {target} | {Colors.BOLD}{dmg} DMG{Colors.RESET} | [Tags: {tag_str}]")
        
    elif event_type == "RESOURCE_DELTA":
        res = data.get('resource', 'Unknown')
        amt = data.get('amount', 0)
        curr = data.get('current_value', 0)
        src = data.get('source', 'Unknown')
        ctx = data.get('context', 'None')
        
        # Agnostic Resource Coloring
        colors = {
            "hp": Colors.RED,
            "stamina": Colors.YELLOW,
            "concentration": Colors.BLUE,
            "fury": Colors.RED,
            "chi": Colors.CYAN,
            "entropy": Colors.MAGENTA,
            "balance": Colors.MAGENTA,
            "heat": Colors.YELLOW
        }
        col = colors.get(str(res).lower(), Colors.CYAN)
        
        print(f"{header} {col}{str(res).upper()}: {amt} ({src}: {ctx}) | Current: {curr}{Colors.RESET}")
        
    elif event_type == "STATUS_CHANGE":
        eff = data.get('effect_id', 'Unknown').upper()
        dur = data.get('duration', 0)
        action = data.get('action', 'unknown')
        
        if action == "applied":
            print(f"{header} {Colors.MAGENTA}STATUS: {eff} APPLIED ({dur}s){Colors.RESET}")
        elif action == "removed":
            print(f"{header} {Colors.MAGENTA}STATUS: {eff} REMOVED{Colors.RESET}")
        elif action == "refreshed":
            print(f"{header} {Colors.MAGENTA}STATUS: {eff} REFRESHED ({dur}s){Colors.RESET}")
            
    elif event_type == "SKILL_EXECUTE":
        skill = data.get('skill', 'Unknown')
        result = data.get('result', '')
        if result:
            print(f"{header} {Colors.GREEN}SKILL: {skill} ({result}){Colors.RESET}")
        else:
            print(f"{header} {Colors.GREEN}SKILL: {skill}{Colors.RESET}")
        
    elif event_type == "RESOURCE_PULSE":
        # Standardized tick-based resource generation feedback
        res = data.get('resource', 'Unknown')
        print(f"{header} {Colors.YELLOW}{res.upper()} PULSE: {data.get('amount', 0)}{Colors.RESET}")
        
    elif event_type == "BUILD_ACTION":
        action = data.get('action', 'Unknown')
        target = data.get('target', 'None')
        coords = data.get('coords', '')
        print(f"{header} {Colors.CYAN}BUILD: {action} on {target} at {coords}{Colors.RESET}")
        
    elif event_type == "BUILD_MARKER":
        label = data.get('label', 'None')
        note = data.get('note', '')
        print(f"{header} {Colors.YELLOW}MARKER: {label} | {note}{Colors.RESET}")
        
    elif event_type == "BUG_REPORT":
        note = data.get('note', '')
        print(f"{header} {Colors.RED}BUG: {note}{Colors.RESET}")
        
    elif event_type == "POSTURE_BREAK":
        print(f"{header} {Colors.RED}*** POSTURE BROKEN! ***{Colors.RESET}")
        
    elif event_type == "COMMAND_EXECUTE":
        cmd = data.get('command', 'Unknown')
        args = data.get('args', '')
        # Don't print passwords to console if we ever log them (though we shouldn't)
        if "password" in cmd.lower(): args = "****"
        print(f"{header} {Colors.YELLOW}CMD: {cmd} {args}{Colors.RESET}")


def _append_to_marks(payload):
    """Appends a markdown-formatted entry to logs/marks.md for AI/Dev consumption."""
    marks_file = "logs/marks.md"
    ts = payload.get("time", "??")
    entity = payload.get("entity", "??")
    room_id = payload.get("room_id", "??")
    data = payload.get("data", {})
    label = data.get("label", "Note")
    note = data.get("note", "")
    coords = data.get("coords", "")
    
    if not os.path.exists(marks_file):
        with open(marks_file, "w", encoding="utf-8") as f:
            f.write("# Godless Development Marks\n\n")
            f.write("A dedicated record of player notes and beacons placed during construction.\n\n")
            
    try:
        with open(marks_file, "a", encoding="utf-8") as f:
            if payload.get("type") == "BUG_REPORT":
                f.write(f"- [{ts}] !! **BUG** !! **{entity}** @ {room_id}: {note}\n")
            else:
                f.write(f"- [{ts}] **{entity}** @ {room_id} {coords}: `{label}` - {note}\n")
    except Exception:
        pass

def log_event(entity, event_type, data=None):
    """
    Logs a structured event to the telemetry log.
    Includes maintenance: Prunes logs every 100 events and routes Marks to marks.md.
    """
    if not hasattr(entity, 'name'):
        return

    # Capture spatial context
    room_id = "Unknown"
    if hasattr(entity, 'room') and entity.room:
        room_id = getattr(entity.room, 'id', "Unknown")

    timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]

    payload = {
        "time": timestamp,
        "entity": entity.name,
        "room_id": room_id,
        "type": event_type,
        "data": data or {}
    }
    
    # Filtering weather/terrain spam from telemetry log
    if event_type == "STATUS_CHANGE":
        eff = str(payload["data"].get("effect_id", "")).lower()
        if eff in ["wet", "cold", "hot", "dry"]:
             return

    telemetry_logger.info(json.dumps(payload))
    
    # Route Construction Events to dedicated log
    if event_type in ["BUILD_ACTION", "BUILD_MARKER", "LOAD_PALETTE"]:
        construction_logger.info(json.dumps(payload))
    
    # Route Markers to dedicated log and markdown
    if event_type == "BUILD_MARKER":
        marker_logger.info(json.dumps(payload))
        _append_to_marks(payload)

    # Route Bugs to dedicated log and markdown
    if event_type == "BUG_REPORT":
        bug_logger.info(json.dumps(payload))
        _append_to_marks(payload)

    # --- Mirror Logging (Console) ---
    _print_console_mirror(entity, event_type, data or {}, timestamp, room_id)

def log_resource_delta(entity, resource, amount, source, context=None):
    """
    Logs a change in resources (HP, Mana, etc).
    """
    # Resolve current value correctly
    current = 0
    if str(resource).upper() == "HP":
        current = getattr(entity, 'hp', 0)
    elif hasattr(entity, 'resources'):
        # Try exact match then lowercase
        current = entity.resources.get(resource, entity.resources.get(str(resource).lower(), 0))
    
    if str(resource).lower() == "balance":
        col = Colors.MAGENTA
    else:
        col = Colors.CYAN
        
    if amount == 0:
        return

    log_event(entity, "RESOURCE_DELTA", {
        "resource": resource,
        "amount": amount,
        "source": source,
        "context": context,
        "current_value": current
    })

def log_posture_break(entity):
    """
    Logs when a target's posture bar hits zero.
    """
    log_event(entity, "POSTURE_BREAK", {})

def log_resource_pulse(entity, resource, amount):
    """Logs standardized resource generation/pulses."""
    log_event(entity, "RESOURCE_PULSE", {"resource": resource, "amount": amount})

def log_status_change(entity, effect_id, action, duration=None):
    """
    Logs status effect application or removal.
    action: 'applied' or 'removed'
    """
    data = {
        "effect_id": effect_id,
        "action": action
    }
    if duration:
        data["duration"] = duration
    
    log_event(entity, "STATUS_CHANGE", data)

def log_stat_snapshot(entity, tags):
    """
    Logs a snapshot of the entity's current stats/tags.
    """
    log_event(entity, "STAT_SNAPSHOT", {
        "tags": tags,
        "active_class": getattr(entity, 'active_class', 'None'),
        "weight_class": getattr(entity, 'weight_class', 'light')
    })

def log_combat_summary(entity, target_name, duration, total_damage, dps):
    """
    Logs a summary of a combat encounter.
    """
    log_event(entity, "COMBAT_SUMMARY", {
        "target": target_name,
        "duration": duration,
        "total_damage": total_damage,
        "dps": dps
    })

def log_vitals(entity):
    """
    Logs a consolidated snapshot of entity vitals.
    Format: [Timestamp] | [Entity] | HP: X/Y | STM: X/Y | Weight: [Class]
    """
    if not hasattr(entity, 'name'):
        return

    hp = f"{getattr(entity, 'hp', 0)}/{getattr(entity, 'max_hp', 0)}"
    
    stm_curr = entity.resources.get("stamina", 0) if hasattr(entity, 'resources') else 0
    stm_max = entity.get_max_resource("stamina") if hasattr(entity, 'get_max_resource') else 100
    stm = f"{stm_curr}/{stm_max}"
    
    w_class = getattr(entity, 'weight_class', 'light').title()
    
    timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
    room_id = getattr(entity.room, 'id', "Unknown") if hasattr(entity, 'room') and entity.room else "Unknown"
    
    header = f"{Colors.WHITE}[{timestamp}] | [{entity.name}] |{Colors.RESET}"
    msg = f"{Colors.RED}HP: {hp}{Colors.RESET} | {Colors.YELLOW}STM: {stm}{Colors.RESET} | {Colors.CYAN}Weight: {w_class}{Colors.RESET}"
    
    print(f"{header} {msg}")
    
    # Also log to file
    payload = {
        "time": timestamp,
        "entity": entity.name,
        "room_id": room_id,
        "type": "VITALS",
        "data": {"hp": hp, "stamina": stm, "weight": w_class}
    }
    telemetry_logger.info(json.dumps(payload))

def log_build_action(player, action, target_id, coords=None):
    """
    Logs a building event with spatial context for AI comprehension.
    """
    if not coords and hasattr(player, 'room') and player.room:
        coords = f"({player.room.x}, {player.room.y}, {player.room.z})"
        
    log_event(player, "BUILD_ACTION", {
        "action": action,
        "target": target_id,
        "coords": coords
    })

def log_build_marker(player, label, note=""):
    """
    Drops a named beacon for AI design requests.
    """
    if not hasattr(player, 'room') or not player.room:
        return
        
    coords = f"({player.room.x}, {player.room.y}, {player.room.z})"
    log_event(player, "BUILD_MARKER", {
        "label": label,
        "note": note,
        "coords": coords,
        "room_id": player.room.id
    })

def log_bug_report(player, note):
    """
    Records a developer bug report.
    """
    coords = f"({player.room.x}, {player.room.y}, {player.room.z})" if hasattr(player, 'room') and player.room else "Unknown"
    log_event(player, "BUG_REPORT", {
        "note": note,
        "coords": coords
    })

def log_command(player, command, args):
    """
    Records a player command for diagnostic auditing.
    """
    log_event(player, "COMMAND_EXECUTE", {
        "command": command,
        "args": args
    })
