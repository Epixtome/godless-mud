from .combat import auto_attack, process_death, reset_round_counters
from .regen import passive_regen, process_rest
from .decay import register_decay, initialize_decay, decay
from .weather import weather, time_of_day
from .ai import mob_ai
from .environmental import monitor_terrain
from . import status


def get_heartbeat_subscribers():
    """Returns the list of functions to call every heartbeat."""
    from logic.core import effects
    from logic import mob_manager
    return [
        effects.process_effects,
        auto_attack,
        process_death,
        process_rest,
        passive_regen,
        decay,
        weather,
        time_of_day,
        mob_ai,
        monitor_terrain,
        mob_manager.check_respawns
    ]
