"""
logic/systems.py (Compatibility Shim V5.0)
This file redirects to the sharded modules in logic/core/systems/.
"""
from .core.systems import (
    auto_attack,
    process_death,
    reset_round_counters,
    passive_regen,
    process_rest,
    register_decay,
    initialize_decay,
    decay,
    weather,
    time_of_day,
    mob_ai,
    monitor_terrain
)
