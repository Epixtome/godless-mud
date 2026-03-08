import logging
import json
import os
from utilities.colors import Colors
from utilities import telemetry
from logic.core.engines import event_engine

logger = logging.getLogger("GodlessMUD")

STATUS_MAP = {
    'hidden': 'concealed',
    'sneaking': 'concealed',
    'stealth': 'concealed'
}

# Status Hierarchy
CRITICAL_STATES = {"prone", "off_balance", "jarred", "stun"}
HARD_DEBUFFS = {"shocked", "overheated", "webbed", "frozen", "silence", "disarmed"}
SOFT_DEBUFFS = {"wet", "cold", "muddy", "bleed", "corroded", "blind", "panting"}

# Define the Schema explicitly to prevent KeyErrors
CORE_STATUS_DEFINITIONS = {
    "prone": {
        "name": "Prone",
        "blocks": ["movement", "combat", "skills"],
        "description": "Knocked to the ground. You must 'stand' to act.",
        "metadata": {
            "is_debuff": True
        }
    },
    "panting": {
        "name": "Panting",
        "blocks": ["combat", "skills"],
        "description": "Gasping for breath from over-exertion.",
        "metadata": {
            "is_debuff": True
        }
    },
    "exhausted": {
        "name": "Exhausted",
        "blocks": [],
        "description": "Movement is significantly slowed due to over-exertion.",
        "metadata": {
            "is_debuff": True
        }
    },
    "stalled": {
        "name": "Stalled",
        "blocks": ["movement"],
        "description": "Momentarily stopped by physical friction.",
        "metadata": {
            "is_debuff": True
        }
    },
    "dazed": {
        "name": "Dazed",
        "blocks": ["combat"],
        "description": "Reeling from a heavy blow. Cannot attack.",
        "metadata": {
            "is_debuff": True
        }
    },
    "overheated": {
        "name": "Overheated",
        "blocks": ["movement", "combat"],
        "metadata": {
            "is_debuff": True
        }
    },
    "turtle_stance": {
        "name": "Turtle Stance",
        "description": "A defensive stance granting immunity to knockdowns.",
        "metadata": {
            "immune_to": ["prone", "knockback"]
        }
    },
    "wet": {
        "name": "Wet",
        "description": "Soaked with water. Lightning damage may be increased.",
        "metadata": {
            "is_debuff": True
        }
    },
    "atrophy": {
        "name": "Atrophy",
        "description": "Your muscles waste away. Stamina regeneration is disabled.",
        "blocks": ["stamina_regen"],
        "metadata": {
            "is_debuff": True
        }
    }
}

def apply_effect(target, effect_id, duration, verbose=True, log_event=True):
    """
    Applies a status effect to the target, respecting hierarchy rules.
    """
    if not target:
        return

    # Legacy Mapping
    if effect_id in STATUS_MAP:
        effect_id = STATUS_MAP[effect_id]

    # --- LOGIC GATES (Data-Driven) ---
    # Check for Immunities in active effects
    if hasattr(target, 'status_effects'):
        game = getattr(target, 'game', None)
        for active_id in target.status_effects:
            active_def = get_effect_definition(active_id, game)
            if active_def:
                # Check metadata for 'immune_to' list
                immune_list = active_def.get('metadata', {}).get('immune_to', [])
                if effect_id in immune_list:
                    if hasattr(target, 'send_line'):
                        target.send_line(f"{Colors.YELLOW}[!] You are immune to that effect!{Colors.RESET}")
                    return

    # 1. Critical State Exclusivity Rule
    # A player can only have ONE Critical State at a time.
    if effect_id in CRITICAL_STATES:
        # Remove any existing critical state (The new one overrides)
        to_remove = [eff for eff in target.status_effects if eff in CRITICAL_STATES and eff != effect_id]
        for eff in to_remove:
            remove_effect(target, eff, verbose=False)

    # Calculate Expiry (Integration with existing system)
    game = getattr(target, 'game', None)
    expiry = duration
    if game:
        expiry = game.tick_count + duration

    # Apply/Update Effect
    if not hasattr(target, 'status_effects'):
        target.status_effects = {}
        
    # Track start tick for persistence checks
    if not hasattr(target, 'status_effect_starts'):
        target.status_effect_starts = {}
    
    game = getattr(target, 'game', None)
    current_tick = game.tick_count if game else 0
    target.status_effect_starts[effect_id] = current_tick

    action = "applied"
    if effect_id in target.status_effects:
        action = "refreshed"
        
    target.status_effects[effect_id] = expiry
    if log_event:
        telemetry.log_status_change(target, effect_id, action, duration)

def remove_effect(target, effect_id, verbose=True):
    """Removes a status effect."""
    # Persistence Check: Prone cannot be removed in the same tick it was applied
    if effect_id == "prone":
        game = getattr(target, 'game', None)
        current_tick = game.tick_count if game else 0
        start_tick = getattr(target, 'status_effect_starts', {}).get(effect_id, -1)
        
        if start_tick == current_tick:
            if verbose and hasattr(target, 'send_line'):
                target.send_line(f"{Colors.RED}You are too off-balance to recover yet!{Colors.RESET}")
            return False

    if effect_id in target.status_effects:
        del target.status_effects[effect_id]
        telemetry.log_status_change(target, effect_id, "removed")
        if verbose and hasattr(target, 'send_line') and effect_id != "panting":
            target.send_line(f"{Colors.CYAN}You are no longer {effect_id.replace('_', ' ')}.{Colors.RESET}")
            
        # Dispatch Event
        event_engine.dispatch("on_status_removed", {
            "player": target,
            "status_id": effect_id
        })
        
        return True
    return False

def has_effect(target, effect_id):
    """Checks if target has a specific effect."""
    return effect_id in getattr(target, 'status_effects', {})

def process_effects(game):
    """Called by the heartbeat to manage effect expiry."""
    # Process Players
    for entity in list(game.players.values()):
        _process_entity_effects(game, entity)
        
    # Process Mobs (Iterate rooms to find active mobs)
    for room in game.world.rooms.values():
        for entity in list(room.monsters):
            if getattr(entity, 'pending_death', False):
                continue
            _process_entity_effects(game, entity)

def _process_entity_effects(game, entity):
    # Handle Pending Skills (Buttery Execution)
    if hasattr(entity, 'pending_skill') and entity.pending_skill:
        skill = entity.pending_skill['skill']
        args = entity.pending_skill['args']
        
        # Check if cooldown expired
        current_tick = game.tick_count
        cd_expiry = getattr(entity, 'cooldowns', {}).get(skill.id, 0)
        
        if current_tick >= cd_expiry:
            del entity.pending_skill
            from logic.commands import skill_commands
            if hasattr(entity, 'send_line'):
                entity.send_line(f"{Colors.GREEN}Unleashing buffered skill: {skill.name}{Colors.RESET}")
            skill_commands._execute_skill(entity, skill, args)

    if not hasattr(entity, 'status_effects') or not entity.status_effects:
        return

    expired_effects = []
    for effect_id, expiry_tick in entity.status_effects.items():
        # 1. Handle Expiry
        if expiry_tick is None:
            continue # Indefinite effect, managed by specific logic (e.g. Resource Engine)
            
        if game.tick_count >= expiry_tick:
            expired_effects.append(effect_id)
            continue
        
        effect_data = game.world.status_effects.get(effect_id)
        
        # 2. Dispatch Tick Event
        # Listeners can set 'expire_now' in ctx to force removal (e.g. broken concentration)
        ctx = {
            'game': game,
            'entity': entity,
            'effect_id': effect_id,
            'effect_data': effect_data,
            'expire_now': False
        }
        from logic.core.engines import event_engine
        event_engine.dispatch("effect_tick", ctx)
        
        if ctx['expire_now']:
            expired_effects.append(effect_id)

    for effect_id in expired_effects:
        remove_effect(entity, effect_id)

def get_effect_definition(effect_id, game):
    """
    Single Source of Truth for effect data.
    Checks Core Registry first, then falls back to JSON DB.
    """
    # 1. Check Hardcoded Core Statuses
    if effect_id in CORE_STATUS_DEFINITIONS:
        return CORE_STATUS_DEFINITIONS[effect_id]

    # 2. Check External JSON Database
    if game and hasattr(game, 'world'):
        definition = game.world.status_effects.get(effect_id)
        if definition:
            return definition
            
        # 3. Lazy Load from Disk (Fallback)
        # Solves "Status definition missing" if the loader hasn't run or file is new.
        file_path = f"data/status_effects/{effect_id}.json"
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    if 'id' in data:
                        game.world.status_effects[effect_id] = data
                        logger.info(f"Lazy-loaded status effect: {effect_id}")
                        return data
            except Exception as e:
                logger.error(f"Failed to lazy-load {effect_id}: {e}")

    return None

def get_status_help(keyword, game):
    """
    Retrieves a help-compatible dictionary for a status effect.
    Searches both CORE definitions and World (JSON) definitions.
    """
    keyword = keyword.lower().strip()
    
    # 1. Try Direct ID Match
    defn = get_effect_definition(keyword, game)
    
    # 2. Try Name Match (Iterative)
    if not defn:
        # Check Core
        for k, v in CORE_STATUS_DEFINITIONS.items():
            if v.get('name', '').lower() == keyword:
                defn = v
                break
        
        # Check Game World (JSON loaded)
        if not defn and game and hasattr(game, 'world'):
            for k, v in game.world.status_effects.items():
                if v.get('name', '').lower() == keyword:
                    defn = v
                    break
    
    if defn:
        name = defn.get('name', keyword.title())
        desc = defn.get('description', "No description available.")
        
        # Append Metadata details
        extras = []
        
        blocks = defn.get('blocks', [])
        if blocks:
            extras.append(f"Blocks: {', '.join(blocks).title()}")
            
        mods = defn.get('modifiers', {})
        if mods:
            mod_list = [f"{k.replace('_', ' ').title()}: {v}" for k, v in mods.items()]
            extras.append(f"Modifiers: {', '.join(mod_list)}")
            
        if extras:
            desc += "\n\n" + "\n".join(extras)
            
        return {
            "keywords": [keyword, name.lower()],
            "title": f"Status: {name}",
            "body": desc,
            "category": "status"
        }
        
    return None

def is_movement_command(cmd_name):
    """Checks if a command is for movement."""
    return cmd_name in ["n", "s", "e", "w", "u", "d", "north", "south", "east", "west", "up", "down", "ne", "nw", "se", "sw", "enter", "leave", "move", "flee"]

def is_combat_command(cmd_name):
    """Checks if a command is for combat."""
    return cmd_name in ["kill", "k", "attack", "hit", "cast", "shoot", "throw"]

def is_skill_command(cmd_name):
    """Checks if a command is a skill activation."""
    # This can be expanded, but covers the core MVP skills
    # DEPRECATED: This is now handled by _is_skill_command for dynamic resolution.
    return False

def _is_skill_command(player, cmd_name):
    """Checks if a command string corresponds to an equipped skill or a skill-casting command."""
    # Generic commands that execute skills
    if cmd_name in ["cast", "sing"]:
        return True

    if not hasattr(player, 'equipped_blessings'):
        return False

    # Check against equipped blessings by ID or name
    return any(b.id == cmd_name or b.name.lower() == cmd_name for b_id in player.equipped_blessings if (b := player.game.world.blessings.get(b_id)))

def is_action_blocked(player, cmd_name):
    """
    Checks if the current status effects block the attempted command.
    Returns (True, Reason) or (False, None).
    """
    if not hasattr(player, 'game') or not player.game:
        return False, None

    cmd_name = cmd_name.lower()
    active_effects = getattr(player, 'status_effects', {})

    # Check each active effect
    for effect_id in active_effects:
        effect_def = get_effect_definition(effect_id, player.game)

        if not effect_def:
            logger.error(f"Status definition missing for ID: {effect_id} on player {player.name}")
            continue

        blocked_types = effect_def.get('blocks', [])
        effect_name = effect_def.get('name', effect_id.replace('_', ' '))

        if "movement" in blocked_types and is_movement_command(cmd_name):
            return True, f"You cannot move while {effect_name.lower()}!"
        if "combat" in blocked_types and is_combat_command(cmd_name):
            return True, f"You cannot fight while {effect_name.lower()}!"
        if "skills" in blocked_types and _is_skill_command(player, cmd_name):
            return True, f"You cannot use skills while {effect_name.lower()}!"

    return False, None
