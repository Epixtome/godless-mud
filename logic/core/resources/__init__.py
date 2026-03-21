"""
logic/core/resources/__init__.py
Unified Resource Management (URM) Facade.
V7.2 Standard: Sharded into micro-modules to respect the 300-line limit.
"""
from .vitals import update_max_hp
from .modify import modify_resource, get_resource, get_max_resource
from .stamina import calculate_stamina_regen
from .mana import calculate_conc_regen
from .posture import calculate_balance_regen, calculate_heat_decay
from .tick import process_tick

def calculate_total_weight(entity):
    """
    [DEPRECATED] Use logic.core.utils.player_logic.calculate_total_weight instead.
    """
    from logic.core.utils import player_logic
    return player_logic.calculate_total_weight(entity, only_equipped=True)

# Re-exports for cleaner imports
__all__ = [
    'update_max_hp',
    'modify_resource',
    'get_resource',
    'get_max_resource',
    'calculate_stamina_regen',
    'calculate_conc_regen',
    'calculate_balance_regen',
    'calculate_heat_decay',
    'process_tick',
    'calculate_total_weight'
]
