"""
logic/core/combat.py
Unified Facade for the Godless Combat System.
Decouples engines from the business logic layer.
All business logic results are delegated to combat_logic.py.
"""
from typing import TYPE_CHECKING, List, Set, Optional, Any
from logic.core.utils import combat_logic

if TYPE_CHECKING:
    from models.entities.player import Player

def resolve_attack_tags(attacker: Any, blessing: Any = None) -> set:
    """Synthesizes a master set of tags for a combat action."""
    return combat_logic.resolve_attack_tags(attacker, blessing)

def calculate_base_damage(attacker: Any, target: Any, blessing: Any = None) -> int:
    """Calculates the raw base damage before events and modifiers."""
    return combat_logic.calculate_base_damage(attacker, target, blessing)

def get_attack_verb(damage_percent: float) -> str:
    """Determines the verb used in combat messages based on damage severity."""
    return combat_logic.get_attack_verb(damage_percent)

def calculate_damage(attacker: Any, victim: Optional[Any] = None, blessing: Any = None) -> int:
    """Calculates final damage for an attack, respecting modifiers and armor."""
    return combat_logic.calculate_damage(attacker, victim, blessing)

def calculate_hit_result(attacker: Any, target: Any, accuracy: int, tags: Set[str]) -> bool:
    """Calculates whether a combat action hits its target."""
    return combat_logic.calculate_hit_result(attacker, target, accuracy, tags)

def handle_attack(attacker: Any, victim: Any, room: Any, game: Any, blessing: Optional[Any] = None, context_prefix: Optional[str] = None) -> List[Any]:
    """Executes a single combat exchange and processes results."""
    from logic.engines import combat_actions
    prompts: Set[Any] = set()
    combat_actions.execute_attack(attacker, victim, room, game, prompts, blessing=blessing, context_prefix=context_prefix)
    return list(prompts)

def distribute_rewards(player: 'Player', victim: Any, game: Any) -> None:
    """Awards Favor, XP, or Soul fragments for a kill."""
    combat_logic.distribute_favor(player, victim, game)

def distribute_favor(player: 'Player', target: Any, game: Any) -> None:
    """Standardized entry for favor distribution."""
    combat_logic.distribute_favor(player, target, game)

def is_target_valid(attacker: Any, target: Any) -> bool:
    """Checks if combat between two entities is possible (distance, HP, structure)."""
    return combat_logic.is_target_valid(attacker, target)

def kill_entity(victim: Any, killer: Optional[Any] = None) -> None:
    """Dispatches a global death event to trigger the reaper phase."""
    from logic.core import event_engine
    event_engine.dispatch("on_death", {'victim': victim, 'killer': killer})

def get_combat_rating(entity: Any) -> float:
    """Returns the total power measurement (GCR) of an entity."""
    return combat_logic.get_combat_rating(entity)

def estimate_player_damage(player: 'Player') -> int:
    """Estimates average damage for the consider command."""
    return combat_logic.estimate_player_damage(player)

def get_crit_chance(player: 'Player') -> float:
    """Calculates critical hit chance for the player based on Kit."""
    return combat_logic.get_crit_chance(player)

def get_defense_rating(entity: Any) -> int:
    """Calculates total defense for any entity (Player or Mob)."""
    return combat_logic.get_defense_rating(entity)

def apply_damage(target: Any, amount: int, source: Any = None, context: str = "Combat", tags: Optional[Set[str]] = None) -> int:
    """Standardized pipeline for applying damage to any entity."""
    return combat_logic.apply_damage(target, amount, source=source, context=context, tags=tags)

def can_act(entity: Any) -> bool:
    """Checks if an entity is capable of taking a combat action."""
    return combat_logic.can_act(entity)

def handle_target_loss(entity: Any) -> Any:
    """Handles logic when an entity loses their target."""
    return combat_logic.handle_target_loss(entity)

def start_combat(player: 'Player', target: Any) -> None:
    """Initiates combat between two entities, handling symmetry and interrupts."""
    combat_logic.start_combat(player, target)

def stop_combat(entity: Any) -> None:
    """Safely ends combat for an entity."""
    combat_logic.stop_combat(entity)

def calculate_difficulty(player: 'Player', target: Any) -> str:
    """Returns a human-readable string describing the threat level of a target."""
    return combat_logic.calculate_difficulty(player, target)

def flee(entity: Any) -> bool:
    """Executes a flee attempt for a player or monster."""
    from .systems import flee as flee_sys
    return flee_sys.handle_flee(entity)

# --- LEGACY ALIASES ---
calculate_player_damage = calculate_base_damage
calculate_mob_damage = calculate_base_damage
estimate_crit_chance = get_crit_chance
estimate_defense = get_defense_rating
validate_target = is_target_valid
