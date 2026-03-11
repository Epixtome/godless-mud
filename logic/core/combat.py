"""
logic/core/combat.py
Unified Facade for the Godless Combat System.
Decouples engines from the business logic layer.
"""
from typing import TYPE_CHECKING, List, Set, Optional, Any
from logic.core import event_engine
from logic.core.utils import combat_logic

if TYPE_CHECKING:
    from models.entities.player import Player

def resolve_attack_tags(attacker: Any, blessing: Any = None) -> set:
    """Synthesizes a master set of tags for a combat action."""
    return combat_logic.resolve_attack_tags(attacker, blessing)

def calculate_base_damage(attacker: Any, target: Any, blessing: Any = None) -> int:
    """Calculates the raw base damage before events and modifiers."""
    from logic.engines import blessings_engine
    from logic import calibration
    
    raw_damage = 0
    if blessing:
        raw_damage = blessings_engine.calculate_power(blessing, attacker, target)
    elif hasattr(attacker, 'equipped_weapon') and hasattr(attacker, 'current_tags'):
        if attacker.equipped_weapon:
            weapon_dmg = blessings_engine.calculate_weapon_power(attacker.equipped_weapon, attacker)
            scaling = getattr(attacker.equipped_weapon, 'scaling', {})
            if not scaling and hasattr(attacker.equipped_weapon, 'stats'):
                scaling = attacker.equipped_weapon.stats.get('scaling', {})
            
            scale_tag = scaling.get('tag', 'martial')
            scale_mult = scaling.get('mult', 1.0)
            tag_val = attacker.current_tags.get(scale_tag, 0)
            power_mult = 1.0 + (tag_val * calibration.CombatBalance.VOLTAGE_SCALING * scale_mult)
            raw_damage = int(weapon_dmg * power_mult)
        else:
            raw_damage = 1 # Unarmed base

        attack_tags = resolve_attack_tags(attacker, blessing)
        ctx = {'attacker': attacker, 'target': target, 'damage': raw_damage, 'tags': attack_tags}
        event_engine.dispatch("calculate_base_damage", ctx)
        raw_damage = ctx['damage']
    elif hasattr(attacker, 'damage'):
        raw_damage = getattr(attacker, 'damage', 1)
        ctx = {'attacker': attacker, 'target': target, 'damage': raw_damage}
        event_engine.dispatch("calculate_base_damage", ctx)
        raw_damage = ctx['damage']
            
    return max(1, int(raw_damage))

def get_attack_verb(damage_percent: float) -> str:
    """Determines the verb used in combat messages based on damage severity."""
    return combat_logic.get_attack_verb(damage_percent)

def calculate_damage(attacker: Any, victim: Optional[Any] = None) -> int:
    """Calculates final damage for an attack, respecting modifiers and armor."""
    raw = calculate_base_damage(attacker, victim)
    defense = get_defense_rating(victim) if victim else 0
    return max(1, raw - defense)

def handle_attack(attacker: Any, victim: Any, room: Any, game: Any, blessing: Optional[Any] = None) -> List[Any]:
    """Executes a single combat exchange and processes results."""
    from logic.engines import combat_actions
    prompts: Set[Any] = set()
    combat_actions.execute_attack(attacker, victim, room, game, prompts, blessing=blessing)
    return list(prompts)

def distribute_rewards(player: 'Player', victim: Any, game: Any) -> None:
    """Awards Favor, XP, or Soul fragments for a kill."""
    combat_logic.distribute_favor(player, victim, game)

def distribute_favor(player: 'Player', target: Any, game: Any) -> None:
    """Standardized entry for favor distribution."""
    combat_logic.distribute_favor(player, target, game)

def is_target_valid(attacker: Any, target: Any) -> bool:
    """Checks if combat between two entities is possible (distance, HP, structure)."""
    if not target or getattr(target, 'hp', 0) <= 0: return False
    
    # Strict Schema Validation (Clean Border API)
    required_attrs = ['hp', 'name', 'room']
    if not all(hasattr(target, attr) for attr in required_attrs):
        return False
        
    if hasattr(attacker, 'room') and hasattr(target, 'room'):
        if attacker.room != target.room: return False
        
    return True

def kill_entity(victim: Any, killer: Optional[Any] = None) -> None:
    """Dispatches a global death event to trigger the reaper phase."""
    event_engine.dispatch("on_death", {'victim': victim, 'killer': killer})

def estimate_player_damage(player: 'Player') -> int:
    """Estimates average damage for the consider command."""
    return combat_logic.estimate_player_damage(player)

def get_crit_chance(player: 'Player') -> float:
    """Calculates critical hit chance for the player based on Kit."""
    return combat_logic.get_crit_chance(player)

def get_defense_rating(entity: Any) -> int:
    """Calculates total defense for any entity (Player or Mob)."""
    return combat_logic.get_defense_rating(entity)

def apply_damage(target: Any, amount: int, source: Any = None, context: str = "Combat") -> int:
    """Standardized pipeline for applying damage to any entity."""
    ctx = {'target': target, 'damage': amount, 'source': source, 'context': context}
    event_engine.dispatch("on_take_damage", ctx)
    actual_damage = ctx['damage']
    if hasattr(target, 'hp'):
        target.hp = max(0, target.hp - actual_damage)
        if target.hp <= 0:
            event_engine.dispatch("on_death", {'victim': target, 'killer': source, 'debug_source': f"Combat.apply_damage({context})"})
    return actual_damage

def can_act(entity: Any) -> bool:
    """Checks if an entity is capable of taking a combat action (not stunned, resting, etc)."""
    if getattr(entity, 'hp', 0) <= 0 or getattr(entity, 'pending_death', False):
        return False
    is_stunned = "stun" in getattr(entity, 'status_effects', {})
    state = getattr(entity, 'state', 'normal')
    return not (is_stunned or state in ["stunned", "casting", "resting"])

def handle_target_loss(entity: Any) -> Any:
    """Handles logic when an entity loses their target."""
    from utilities.colors import Colors
    target = getattr(entity, 'fighting', None)
    if target and getattr(target, 'hp', 0) <= 0 and getattr(target, 'pending_death', False):
        return target
    valid_attackers = [a for a in getattr(entity, 'attackers', []) if is_target_valid(entity, a)]
    if valid_attackers:
        new_target = valid_attackers[0]
        entity.fighting = new_target
        if hasattr(entity, 'send_line'):
            entity.send_line(f"{Colors.YELLOW}You turn to fight {new_target.name}!{Colors.RESET}")
        return new_target
    if hasattr(entity, 'send_line') and entity.fighting:
        entity.send_line(f"You are no longer fighting.")
    stop_combat(entity)
    return None

def start_combat(player: 'Player', target: Any) -> None:
    """Initiates combat between two entities, handling symmetry and interrupts."""
    # Handle switching targets (Clean up old observers)
    old_target = getattr(player, 'fighting', None)
    if old_target and old_target != target and hasattr(old_target, 'attackers'):
        if player in old_target.attackers:
            old_target.attackers.remove(player)

    player.fighting = target
    player.state = "combat"
    if hasattr(target, 'fighting'):
        if hasattr(target, 'attackers') and player not in target.attackers:
            target.attackers.append(player)
        if not getattr(target, 'fighting', None):
            target.fighting = player
        if hasattr(target, 'interaction_context') and target.interaction_context:
            target.interaction_context.shatter(target)

def stop_combat(entity: Any) -> None:
    """Safely ends combat for an entity."""
    combat_logic.stop_combat(entity)

def calculate_difficulty(player: 'Player', target: Any) -> str:
    """Returns a human-readable string describing the threat level of a target."""
    return combat_logic.calculate_difficulty(player, target)

# --- LEGACY ALIASES ---
calculate_player_damage = calculate_base_damage
calculate_mob_damage = calculate_base_damage
estimate_crit_chance = get_crit_chance
estimate_defense = get_defense_rating
validate_target = is_target_valid
