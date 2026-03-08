import random
from utilities.colors import Colors
from logic.core import status_effects_engine

WEATHER_TABLE = {
    "default": ["clear", "cloudy", "rain"],
    "kingdom_light": ["clear", "sunny", "blinding_light"],
    "kingdom_dark": ["foggy", "dark_mist", "void_storm"],
    "kingdom_instinct": ["overcast", "rain", "thunderstorm"]
}

def weather(game):
    """Updates weather per zone."""
    if game.tick_count % 50 != 0:
        return
        
    for zone in game.world.zones.values():
        options = WEATHER_TABLE.get(zone.id, WEATHER_TABLE["default"])
        new_weather = random.choice(options)
        
        WEATHER_TO_STATUS = {
            "storm": ("wet", 60),
            "rain": ("wet", 30),
            "blizzard": ("cold", 30),
            "sandstorm": ("blind", 10),
            "heatwave": ("exhausted", 10)
        }

        for room in game.world.rooms.values():
            if room.zone_id == zone.id:
                if room.players:
                    for p in room.players:
                        p.send_line(f"{Colors.CYAN}The weather shifts to {new_weather.replace('_', ' ')}.{Colors.RESET}")
                
                if new_weather in WEATHER_TO_STATUS:
                    status_id, duration = WEATHER_TO_STATUS[new_weather]
                    for entity in room.players + room.monsters:
                        status_effects_engine.apply_effect(entity, status_id, duration)

def time_of_day(game):
    """Updates global time."""
    cycle = game.tick_count % 300
    
    msg = None
    if cycle == 0:
        msg = "The sun rises in the east."
    elif cycle == 75:
        msg = "The sun climbs high into the sky."
    elif cycle == 150:
        msg = "The sun begins to set."
    elif cycle == 225:
        msg = "Night falls across the land."
        
    if msg:
        for p in game.players.values():
            p.send_line(f"{Colors.YELLOW}{msg}{Colors.RESET}")
