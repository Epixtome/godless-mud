from .combat import auto_attack, process_death, reset_round_counters
from .regen import passive_regen, process_rest
from .decay import register_decay, initialize_decay, decay
from .weather import weather_pulse, time_of_day
from .ai import mob_ai
from .environmental import monitor_terrain
from . import engagement
from . import status
from . import battle_logger

# Initialize non-heartbeat systems
engagement.initialize()
battle_logger.initialize()

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
        weather_pulse,
        time_of_day,
        mob_ai,
        monitor_terrain,
        mob_manager.check_respawns,
        battle_logger.flush_inactive_encounters
    ]
