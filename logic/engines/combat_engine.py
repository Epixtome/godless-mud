import random
import logging
from logic.core import event_engine
from utilities.utils import roll_dice
from logic.core import status_effects_engine
from logic.engines.resonance_engine import ResonanceAuditor
from logic import calibration

logger = logging.getLogger("GodlessMUD")

# get_resonance_bonus removed (Tag Scaling Disabled)

def calculate_player_damage(player, target=None):
    """Calculates damage for a player's auto-attack."""
    from logic.engines import blessings_engine
    damage = 0
    
    from logic.engines import combat_math
    
    if player.equipped_weapon:
        # 1. Base Weapon Dice
        weapon_dmg = blessings_engine.calculate_weapon_power(player.equipped_weapon, player)
        
        # 2. Scaling (Martial, Speed, Precision, etc.)
        scaling = getattr(player.equipped_weapon, 'scaling', {})
        if not scaling and hasattr(player.equipped_weapon, 'stats'):
            scaling = player.equipped_weapon.stats.get('scaling', {})
        
        scale_tag = scaling.get('tag', 'martial') # Fallback to martial
        scale_mult = scaling.get('mult', 1.0)
        
        # Get Tag Value from Player's Resonance
        tag_val = player.current_tags.get(scale_tag, 0)
        
        # Power = Base * (1 + (Tag * Scaling_Factor) * Mult)
        # e.g., 10 Martial * 0.10 = 1.0 (100% bonus) -> 2x Damage
        power_mult = 1.0 + (tag_val * calibration.CombatBalance.VOLTAGE_SCALING * scale_mult)
        damage = int(weapon_dmg * power_mult)
    else:
        # Unarmed Base (Monk logic will override via event)
        damage = 1
    
    # Identify Attack Tags for Event Handlers
    attack_tags = set()
    if player.equipped_weapon:
        w_tags = getattr(player.equipped_weapon, 'gear_tags', [])
        if isinstance(w_tags, list): attack_tags.update(w_tags)
        elif isinstance(w_tags, dict): attack_tags.update(w_tags.keys())
    else:
        attack_tags.add("martial")
        attack_tags.add("unarmed")
    
    # Dispatch Event for Modifiers (Passives, Buffs)
    ctx = {'attacker': player, 'target': target, 'damage': damage, 'tags': attack_tags}
    event_engine.dispatch("calculate_base_damage", ctx)
    damage = ctx['damage']
    
    return max(1, int(damage))

def estimate_player_damage(player):
    """Estimates average damage for the consider command."""
    from logic.engines import blessings_engine
    damage = 0
    
    if player.equipped_weapon:
        damage = blessings_engine.calculate_weapon_power(player.equipped_weapon, player, avg=True)
    else:
        damage = 1
        
    return damage

def estimate_crit_chance(player):
    """Estimates critical hit chance based on Kit."""
    # Base 5%
    chance = 5.0
    if hasattr(player, 'active_kit'):
        chance += player.active_kit.get('crit_bonus', 0)
    
    return min(100.0, chance)

def estimate_defense(player):
    """Returns the player's total defense."""
    if hasattr(player, 'get_defense'):
        return player.get_defense()
    return 0

def calculate_mob_damage(mob, target):
    """Calculates damage dealt by a mob to a player."""
    raw = mob.damage
    
    # True Damage Check (Magic, Bleed, etc. ignore defense)
    is_true_damage = False
    if hasattr(mob, 'tags') and any(t in mob.tags for t in ['magic', 'bleed', 'true_damage']):
        is_true_damage = True
        
    defense = 0
    if not is_true_damage:
        if hasattr(target, 'get_defense'):
            defense = target.get_defense()
        elif hasattr(target, 'equipped_armor') and target.equipped_armor:
            armor = target.equipped_armor
            if hasattr(armor, 'stats'):
                defense = armor.stats.get('defense', 0)
            else:
                defense = getattr(armor, 'defense', 0)
        
    damage = max(1, raw - defense)
    
    # 3. Dispatch Unified Event (Allows player passives to affect mob damage)
    ctx = {'attacker': mob, 'target': target, 'damage': damage}
    event_engine.dispatch("calculate_base_damage", ctx) # Unify with player event
        
    return ctx['damage']

def distribute_favor(player, target, game):
    """Awards favor to the player based on the kill."""
    tags = getattr(target, 'tags', [])
    if not tags and hasattr(target, 'identity_tags'):
        tags = target.identity_tags

    # Scaling Favor: 1 point per 20 max HP (Minimum 5)
    base_favor = max(5, int(target.max_hp / 20))
    if "avatar" in tags or "boss" in tags:
        base_favor *= 5 # Bosses give significantly more

    # Determine Target Kingdom
    mob_kingdom = None
    if "light" in tags: mob_kingdom = "light"
    elif "dark" in tags: mob_kingdom = "dark"
    elif "instinct" in tags: mob_kingdom = "instinct"
    
    if not mob_kingdom:
        return # Neutral mobs give no favor

    # Award favoring logic: Opposition
    # Dark -> Awards Light
    # Light -> Awards Dark
    # Instinct -> Awards both (slightly) or random? Actually Light is primary Order.
    
    primary_kingdom = None
    secondary_kingdom = None
    
    if mob_kingdom == "dark":
        primary_kingdom = "light"
        secondary_kingdom = "instinct"
    elif mob_kingdom == "light":
        primary_kingdom = "dark"
        secondary_kingdom = "instinct"
    elif mob_kingdom == "instinct":
        # Killing Instinct awards Order (Light) primarily
        primary_kingdom = "light"
        secondary_kingdom = "dark"

    # Distribute to Deities
    all_deities = game.world.deities
    primary_candidates = [d for d in all_deities.values() if d.kingdom == primary_kingdom]
    secondary_candidates = [d for d in all_deities.values() if d.kingdom == secondary_kingdom]

    if primary_candidates:
        # Choose one primary recipient (Full Favor)
        favored = random.choice(primary_candidates)
        player.favor[favored.id] = player.favor.get(favored.id, 0) + base_favor
        player.send_line(f"{Colors.YELLOW}You gain {base_favor} Favor with {favored.name}.{Colors.RESET}")
        
        # Splash small favor to others in primary kingdom (20% of base)
        splash = max(1, int(base_favor * 0.2))
        for d in primary_candidates:
            if d.id != favored.id:
                player.favor[d.id] = player.favor.get(d.id, 0) + splash

    if secondary_candidates:
        # Splash very small favor to secondary kingdom (10% of base)
        splash = max(1, int(base_favor * 0.1))
        for d in secondary_candidates:
            player.favor[d.id] = player.favor.get(d.id, 0) + splash

def validate_target(attacker, target):
    """
    Centralized check to see if a target is valid for combat.
    Returns True if valid, False otherwise.
    """
    if not target: 
        return False
    if target.hp <= 0: 
        # logger.debug(f"Target {target.name} is dead.")
        return False
    if target.room != attacker.room: 
        logger.debug(f"Target {target.name} is in {target.room.id if target.room else 'None'}, attacker in {attacker.room.id if attacker.room else 'None'}")
        return False
    return True