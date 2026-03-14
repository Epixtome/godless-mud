"""
logic/core/utils/combat_logic.py
Internal logic and math for the combat system.
"""
import logging
import random
from typing import Any, List, Set, Optional, TYPE_CHECKING
from utilities.colors import Colors
from logic.constants import Tags
from logic.core import effects
from logic import calibration

if TYPE_CHECKING:
    from models.entities.player import Player
    from models.entities.monster import Monster

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
    if damage_percent >= 0.75:
        return "ERADICATE"
    if damage_percent >= 0.50:
        return "ANNIHILATE"
    if damage_percent >= 0.40:
        return "obliterate"
    if damage_percent >= 0.30:
        return "massacre"
    if damage_percent >= 0.20:
        return "decimate"
    if damage_percent >= 0.10:
        return "maim"
    if damage_percent >= 0.05:
        return "strike"
    return "scratch"

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

def calculate_accuracy(entity: Any) -> int:
    """[V6.0] Calculates total accuracy rating (Base 100)."""
    accuracy = 100
    
    game = getattr(entity, 'game', None)
    for effect_id in getattr(entity, 'status_effects', {}):
        effect_data = effects.get_effect_definition(effect_id, game)
        if isinstance(effect_data, dict):
            metadata = effect_data.get('metadata', {})
            if isinstance(metadata, dict):
                penalty = metadata.get('accuracy_penalty', 0)
                if isinstance(penalty, (int, float)):
                    accuracy -= int(penalty)
    
    return max(0, accuracy)

def stop_combat(entity: Any) -> None:
    """Safely ends combat for an entity and its observers."""
    entity.fighting = None
    if hasattr(entity, 'state') and entity.state == "combat":
        entity.state = "normal"
    
    # 1. Clear my own attackers list
    if hasattr(entity, 'attackers'):
        entity.attackers = []
        
    # 2. Reciprocal Cleanup: Remove myself from other entities' focus
    if hasattr(entity, 'room') and entity.room:
        others = (entity.room.players + entity.room.monsters)
        for other in others:
            if other == entity: continue
            
            # Remove from their attackers list
            if hasattr(other, 'attackers') and entity in other.attackers:
                other.attackers.remove(entity)
            
            # If they are fighting me, they must find a new target or stop
            if hasattr(other, 'fighting') and other.fighting == entity:
                # We don't call stop_combat(other) to avoid recursion, 
                # instead let handle_target_loss deal with it next tick or clear now.
                other.fighting = None
                if hasattr(other, 'state') and other.state == "combat":
                    other.state = "normal"

def start_combat(attacker: Any, target: Any) -> bool:
    """
    Unified Facade for initiating combat between two entities.
    Ensures state transitions and reciprocal updates are handled.
    """
    if not attacker or not target:
        return False
        
    if attacker == target:
        return False
        
    # 1. Set Primary Targeting
    if not attacker.fighting:
        attacker.fighting = target
        
    if hasattr(attacker, 'state'):
        attacker.state = "combat"
        
    # 2. Add to victim's attackers list
    if hasattr(target, 'attackers'):
        if attacker not in target.attackers:
            target.attackers.append(attacker)
            
    # 3. Reciprocal Engagement (Only if not already fighting)
    if not target.fighting:
        # Check for Practice Dummy gate
        tags = getattr(target, 'tags', [])
        is_dummy = "training_dummy" in tags or ("target" in tags and "elite" not in tags and "tactical" not in tags)
        
        if not is_dummy:
            target.fighting = attacker
            if hasattr(target, 'state'):
                target.state = "combat"
                
    return True

def get_weight_class(entity: Any) -> str:
    """[V6.0] Determines Weight Class based on physical LBS (Total Weight)."""
    if not getattr(entity, 'is_player', False):
        # Monsters still use identity tags for classification
        tags = getattr(entity, 'tags', [])
        if "heavy" in tags: return "heavy"
        if "medium" in tags: return "medium"
        return "light"

    from logic.core.utils import player_logic
    from logic import calibration
    
    total_lbs = player_logic.calculate_total_weight(entity, only_equipped=True)
    
    if total_lbs <= calibration.ScalingRules.WEIGHT_LIGHT_MAX:
        return "light"
    if total_lbs <= calibration.ScalingRules.WEIGHT_MEDIUM_MAX:
        return "medium"
    return "heavy"

def get_mitigation_multiplier(entity: Any) -> float:
    """Returns the damage mitigation percentage (0.0 to 1.0) based on weight class."""
    w_class = get_weight_class(entity)
    if w_class == "heavy": return calibration.CombatBalance.BASE_MITIGATION_HEAVY
    if w_class == "medium": return calibration.CombatBalance.BASE_MITIGATION_MEDIUM
    return calibration.CombatBalance.BASE_MITIGATION_LIGHT

def get_stability_rating(entity: Any) -> int:
    """
    Calculates Stability (Resistance to Balance Loss).
    Re-uses old Defense logic but maps it to the Stability domain.
    """
    total_stability = 0
    
    # 1. Gear (Armor & Shield)
    if hasattr(entity, 'equipped_armor') and entity.equipped_armor:
        total_stability += getattr(entity.equipped_armor, 'defense', 0)
    if hasattr(entity, 'equipped_offhand') and entity.equipped_offhand:
        total_stability += getattr(entity.equipped_offhand, 'defense', 0)
        
    # 2. Kit/Stance Bonus
    if hasattr(entity, 'active_kit'):
        kit_mult = entity.active_kit.get('stability_multiplier', 1.0) if isinstance(entity.active_kit, dict) else 1.0
        total_stability = int(total_stability * kit_mult)
    
    # 3. Buffs/Effects
    from logic.core import effects
    game = getattr(entity, 'game', None)
    
    for effect_id in getattr(entity, 'status_effects', {}):
        # Use centralized definition getter (handles game=None via core map)
        effect_data = effects.get_effect_definition(effect_id, game)
        if isinstance(effect_data, dict):
            metadata = effect_data.get('metadata', {})
            if isinstance(metadata, dict):
                # Robust numeric extraction to handle varied metadata types (V4.5 Guard)
                s_add = metadata.get('stability_add', 0)
                if isinstance(s_add, (int, float)):
                    total_stability += int(s_add)
                    
                d_add = metadata.get('defense_add', 0)
                if isinstance(d_add, (int, float)):
                    total_stability += int(d_add)
            
    return int(total_stability)

def check_posture_break(target: Any, damage: float, source: Any = None, tags: Optional[Set[str]] = None):
    """Handles the reduction of Posture and checks for BREAK state."""
    if not hasattr(target, 'resources'): return
    
    tags = tags or set()
    
    # Base Posture Damage
    raw_posture_damage = damage
    
    # [V5.0] Tag-based Posture Modifiers (Daggers & Hammers excel at breaking guard)
    if any(t in tags for t in ["precision", "speed", "blunt", "weight"]):
        raw_posture_damage *= 1.5
    
    # Posture (Balance) is stabilized by the Stability rating
    stability = get_stability_rating(target)
    net_posture_damage = max(1, int(raw_posture_damage - (stability * calibration.CombatBalance.STABILITY_SCALING)))
    
    current_bal = target.resources.get('balance', 100)
    new_bal = max(0, current_bal - net_posture_damage)
    target.resources['balance'] = new_bal
    
    if new_bal <= 0 and current_bal > 0:
        # POSTURE BREAK
        # Apply the 'off_balance' and 'prone' statuses
        effects.apply_effect(target, "off_balance", 4)
        effects.apply_effect(target, "prone", 2)
        
        if hasattr(target, 'send_line'):
            target.send_line(f"{Colors.RED}*** YOUR POSTURE HAS BEEN BROKEN! ***{Colors.RESET}")
        if hasattr(source, 'send_line'):
            source.send_line(f"{Colors.BOLD}{Colors.RED}*** You have SHATTERED {target.name}'s posture! They collapse to the ground! ***{Colors.RESET}")
            
        from utilities import telemetry
        telemetry.log_posture_break(target)
        
        return True
    return False

def get_total_defense(player: 'Player') -> int:
    """[DEPRECATED] Redirects to Stability in V5.0."""
    return get_stability_rating(player)
