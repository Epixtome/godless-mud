"""
logic/core/utils/combat_logic.py
Internal logic and math for the combat system.
"""
import logging
import random
from typing import Any, List, Set, Optional, TYPE_CHECKING
from utilities.colors import Colors
from logic.constants import Tags
from logic import calibration

if TYPE_CHECKING:
    from models.entities.player import Player

logger = logging.getLogger("GodlessMUD")

def resolve_attack_tags(attacker: Any, blessing: Any = None) -> set:
    """Synthesizes a master set of tags for a combat action."""
    attack_tags = set()
    
    # 1. Base Tags (Weapon/Body)
    if hasattr(attacker, 'equipped_weapon'):
        if attacker.equipped_weapon:
            w_tags = getattr(attacker.equipped_weapon, 'tags', [])
            if isinstance(w_tags, dict):
                attack_tags.update(w_tags.keys())
            elif isinstance(w_tags, list):
                attack_tags.update(w_tags)
        else:
            attack_tags.add(Tags.MARTIAL)
            attack_tags.add(Tags.BLUNT)
    elif hasattr(attacker, 'tags'):
        attack_tags.update(getattr(attacker, 'tags', []))

    # 2. Blessing Overlay
    if blessing:
        b_tags = getattr(blessing, 'identity_tags', [])
        attack_tags.update(b_tags)
        
    return attack_tags

def get_attack_verb(damage_percent: float) -> str:
    """Determines the verb used in combat messages based on damage severity."""
    if damage_percent >= 0.50:
        return "OBLITERATE"
    elif damage_percent >= 0.20:
        return "decimate"
    return "strike"

def estimate_player_damage(player: 'Player') -> int:
    """Estimates average damage for the consider command."""
    from logic.engines import blessings_engine
    damage = 0
    if player.equipped_weapon:
        damage = blessings_engine.calculate_weapon_power(player.equipped_weapon, player, avg=True)
    else:
        damage = 1
    return damage

def get_crit_chance(player: 'Player') -> float:
    """Calculates critical hit chance for the player based on Kit."""
    chance = 5.0 # Base 5%
    if hasattr(player, 'active_kit'):
        chance += player.active_kit.get('crit_bonus', 0)
    return min(100.0, chance)

def distribute_favor(player: 'Player', target: Any, game: Any) -> None:
    """Awards favor to the player based on the kill."""
    tags = getattr(target, 'tags', [])
    if not tags and hasattr(target, 'identity_tags'):
        tags = target.identity_tags

    base_favor = max(5, int(getattr(target, 'max_hp', 100) / 20))
    if "avatar" in tags or "boss" in tags:
        base_favor *= 5

    mob_kingdom = None
    if "light" in tags: mob_kingdom = "light"
    elif "dark" in tags: mob_kingdom = "dark"
    elif "instinct" in tags: mob_kingdom = "instinct"
    
    if not mob_kingdom: return 

    primary_kingdom = None
    secondary_kingdom = None
    
    if mob_kingdom == "dark":
        primary_kingdom = "light"
        secondary_kingdom = "instinct"
    elif mob_kingdom == "light":
        primary_kingdom = "dark"
        secondary_kingdom = "instinct"
    elif mob_kingdom == "instinct":
        primary_kingdom = "light"
        secondary_kingdom = "dark"

    all_deities = game.world.deities
    primary_candidates = [d for d in all_deities.values() if d.kingdom == primary_kingdom]
    secondary_candidates = [d for d in all_deities.values() if d.kingdom == secondary_kingdom]

    if primary_candidates:
        favored = random.choice(primary_candidates)
        player.favor[favored.id] = player.favor.get(favored.id, 0) + base_favor
        player.send_line(f"{Colors.YELLOW}You gain {base_favor} Favor with {favored.name}.{Colors.RESET}")
        
        splash = max(1, int(base_favor * 0.2))
        for d in primary_candidates:
            if d.id != favored.id:
                player.favor[d.id] = player.favor.get(d.id, 0) + splash

    if secondary_candidates:
        splash = max(1, int(base_favor * 0.1))
        for d in secondary_candidates:
            player.favor[d.id] = player.favor.get(d.id, 0) + splash

def calculate_difficulty(player: 'Player', target: Any) -> str:
    """Returns a human-readable string describing the threat level of a target."""
    from logic.core import combat
    p_dmg = combat.calculate_damage(player, target)
    t_dmg = combat.calculate_damage(target, player)
    
    rounds_to_kill = target.hp / max(1, p_dmg)
    rounds_to_die = player.hp / max(1, t_dmg)
    diff = rounds_to_die - rounds_to_kill
    
    if diff > 10: return "You could kill them in your sleep. (Very Easy)"
    if diff > 5: return "You should have no trouble. (Easy)"
    if diff > 0: return "It would be a fair fight. (Even)"
    if diff > -5: return "They look tough. Be careful. (Hard)"
    if diff > -10: return "You would likely die. (Very Hard)"
    return "DEATH_WISH. (Impossible)"

def get_defense_rating(entity: Any) -> int:
    """Calculates total defense for any entity (Player or Mob)."""
    if hasattr(entity, 'get_defense'):
        return entity.get_defense()
    return 0

def stop_combat(entity: Any) -> None:
    """Safely ends combat for an entity."""
    entity.fighting = None
    entity.state = "normal"
    if hasattr(entity, 'attackers'):
        entity.attackers = []

def get_total_defense(player: 'Player') -> int:
    """Calculates total defense from Armor, Shields, Kit, and Buffs."""
    total_def = 0
    
    # 1. Armor & Shield
    if hasattr(player, 'equipped_armor') and player.equipped_armor:
        total_def += getattr(player.equipped_armor, 'defense', 0)
    if hasattr(player, 'equipped_offhand') and player.equipped_offhand:
        total_def += getattr(player.equipped_offhand, 'defense', 0)
        
    # 2. Kit Bonus
    if hasattr(player, 'active_kit'):
        kit_mult = player.active_kit.get('defense_multiplier', 1.0) if isinstance(player.active_kit, dict) else 1.0
        total_def = int(total_def * kit_mult)
    
    # 3. Buffs/Effects
    for effect_id in getattr(player, 'status_effects', {}):
        effect_data = player.game.world.status_effects.get(effect_id)
        if effect_data:
            mods = effect_data.get('modifiers', {})
            total_def += mods.get('defense_add', 0)
            
    return min(calibration.MaxValues.DEFENSE, int(total_def))
