import random
import logging
from models import Monster
from utilities.colors import Colors

logger = logging.getLogger("GodlessMUD")

def spawn_mob(room, mob_data, game):
    """Instantiates a mob from data (ID string or dict) and adds to room."""
    if isinstance(mob_data, dict):
        mob_id = mob_data.get('id')
        deltas = mob_data
    else:
        mob_id = mob_data
        deltas = {}

    if mob_id not in game.world.monsters:
        logger.warning(f"Cannot spawn unknown mob ID: {mob_id}")
        return

    if mob_id in game.world.monsters:
        proto = game.world.monsters[mob_id]
        # Clone prototype
        instance = Monster(proto.name, proto.description, proto.hp, proto.damage, 
                           proto.tags, proto.max_hp, prototype_id=mob_id, home_room_id=room.id)
        instance.quests = proto.quests
        instance.can_be_companion = proto.can_be_companion
        instance.cooldowns = {} # Initialize for AI usage
        instance.active_class = None # Initialize for Engine compatibility
        instance.resources = {"stamina": 100, "concentration": 100, "mana": 100} # Initialize resources
        
        # Apply deltas
        for k, v in deltas.items():
            if k != 'id':
                setattr(instance, k, v)
        
        instance.room = room
        instance.game = game
        room.monsters.append(instance)
        room.broadcast(f"A {instance.name} arrives.")
        # logger.info(f"Respawned {instance.name} in {room.id}")

def notify_death(game, mob):
    """Called when a mob dies to schedule a respawn."""
    if not mob.home_room_id or not mob.prototype_id:
        return # Cannot respawn transient mobs
        
    # Schedule respawn (30-60 seconds = 15-30 ticks)
    delay = random.randint(15, 30)
    respawn_tick = game.tick_count + delay
    
    # We need to find the original static definition to respawn correctly
    # For simplicity, we'll just use the prototype ID
    game.world.pending_respawns.append({
        'tick': respawn_tick,
        'room_id': mob.home_room_id,
        'mob_data': mob.prototype_id
    })

def check_respawns(game):
    """Heartbeat task to manage mob respawns."""
    active_timers = []
    for task in game.world.pending_respawns:
        if game.tick_count >= task['tick']:
            room = game.world.rooms.get(task['room_id'])
            if room:
                spawn_mob(room, task['mob_data'], game)
            else:
                logger.debug(f"Skipping respawn for missing room {task['room_id']}")
        else:
            active_timers.append(task)
            
    game.world.pending_respawns = active_timers

def initialize_spawns(game):
    """
    Runs once at startup. 
    Checks all rooms. If a static mob is missing (and not in save file), spawn it.
    """
    logger.info("Initializing world population...")
    for room in game.world.rooms.values():
        if not room.static_monsters:
            continue
            
        # Count active mobs in this room (from save file)
        active_counts = {}
        for m in room.monsters:
            if m.prototype_id:
                active_counts[m.prototype_id] = active_counts.get(m.prototype_id, 0) + 1
            
        for mob_data in room.static_monsters:
            mid = mob_data.get('id') if isinstance(mob_data, dict) else mob_data
            if active_counts.get(mid, 0) > 0:
                active_counts[mid] -= 1
            else:
                # Mob is missing from save (or fresh start), spawn it immediately
                spawn_mob(room, mob_data, game)

def execute_ai_turn(game, mob, target):
    """
    Determines if a mob should perform a special action (Spell/Skill) instead of auto-attacking.
    Returns (did_act, target_died).
    """
    # 1. Check if mob is a caster type
    is_caster = "caster" in mob.tags or "mage" in mob.tags
    is_illusionist = "illusionist" in mob.tags
    is_barbarian = "barbarian" in mob.tags
    is_rogue = "rogue" in mob.tags
    is_monk = "monk" in mob.tags
    is_paladin = "paladin" in mob.tags
    
    if not (is_caster or is_illusionist or is_barbarian or is_rogue or is_monk or is_paladin):
        return False, False

    # 2. Chance to cast (30% per round)
    if random.random() > 0.3:
        return False, False

    # 3. Find a suitable spell from the world definitions
    candidates = []
    for b in game.world.blessings.values():
        if "spell" in b.identity_tags:
            if is_caster and ("fire" in b.identity_tags or "ice" in b.identity_tags or "lightning" in b.identity_tags):
                candidates.append(b)
            elif is_illusionist and ("illusion" in b.identity_tags or "mind" in b.identity_tags):
                candidates.append(b)
        
        elif "skill" in b.identity_tags:
            if is_barbarian and ("rage" in b.identity_tags or "martial" in b.identity_tags):
                # Exclude complex skills that require specific targets/conditions not handled by magic_engine fallback
                if "sunder" not in b.identity_tags and "trip" not in b.identity_tags:
                    # Filter out non-barbarian themes (Light/Dark/Stealth) to prevent using Paladin/Rogue skills
                    if not any(t in b.identity_tags for t in ["light", "dark", "stealth", "rogue", "int"]):
                        candidates.append(b)
            elif is_rogue and ("stealth" in b.identity_tags or "poison" in b.identity_tags):
                candidates.append(b)
            elif is_monk and ("unarmed" in b.identity_tags or "stance" in b.identity_tags):
                candidates.append(b)
            elif is_paladin and ("light" in b.identity_tags or "protection" in b.identity_tags):
                candidates.append(b)
            
    if not candidates:
        return False, False
        
    spell = random.choice(candidates)
    
    # 4. Check Cooldown
    from logic.engines import magic_engine
    ready, _ = magic_engine.check_cooldown(mob, spell, game=game)
    if not ready:
        return False, False
        
    # 5. Execute Cast
    magic_engine.set_cooldown(mob, spell, game=game)
    
    # Calculate Power (Base on Mob Damage * 1.5 for impact)
    power = int(mob.damage * 1.5)
    
    if "spell" in spell.identity_tags:
        mob.room.broadcast(f"{Colors.MAGENTA}{mob.name} begins to chant...{Colors.RESET}")
    else:
        mob.room.broadcast(f"{Colors.RED}{mob.name} prepares to use {spell.name}!{Colors.RESET}")
        
    # Determine target (Self for buffs/stances)
    cast_target = target
    if any(t in spell.identity_tags for t in ["buff", "stance", "protection", "healing", "heal", "mend"]):
        cast_target = mob

    success, msg, target_died = magic_engine.process_spell_effect(mob, cast_target, spell, power, game=game)
    
    return True, target_died