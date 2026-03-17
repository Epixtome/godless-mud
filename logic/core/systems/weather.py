import random
from utilities.colors import Colors
from logic.core import effects

WEATHER_TABLE = {
    "default": ["clear", "cloudy", "rain", "overcast"],
    "aetheria": ["clear", "sunny", "blinding_light", "golden_mist"],
    "umbra": ["foggy", "dark_mist", "void_storm", "shadow_haze"],
    "sylvanis": ["overcast", "rain", "thunderstorm", "pollen_drift"],
    "null_void": ["void_storm", "static_crackle", "reality_blur", "clear"]
}

WEATHER_TO_STATUS = {
    "storm": ("wet", 60),
    "thunderstorm": ("wet", 40),
    "rain": ("wet", 30),
    "blizzard": ("cold", 30),
    "sandstorm": ("blinded", 10),
    "heatwave": ("exhausted", 10),
    "blinding_light": ("blinded", 5),
    "void_storm": ("confused", 10),
    "static_crackle": ("shocked", 5),
    "pollen_drift": ("staggered", 5),
    "dark_mist": ("blinded", 5)
}

def weather(game):
    """
    [V6.0] Optimized Weather Engine.
    Uses Zone-wide global state and Active Room Registry to minimize CPU load.
    Updates every 50 ticks (Approx 100 seconds).
    """
    if game.tick_count % 50 != 0:
        return
        
    # 1. Pre-calculate weather for each zone (Global Shifters)
    shifters = []
    for zone_id in game.world.zones:
        options = WEATHER_TABLE.get(zone_id, WEATHER_TABLE["default"])
        new_weather = random.choice(options)
        old_weather = game.world.zone_weather.get(zone_id)
        
        if new_weather != old_weather:
            game.world.zone_weather[zone_id] = new_weather
            shifters.append(zone_id)
            
    # 2. Update Active Rooms ONLY (Pillar: Modular Efficiency)
    # We iterate over the set of rooms that actually contain entities.
    for room in list(game.world.active_rooms):
        current_weather = game.world.zone_weather.get(room.zone_id, "clear")
        
        # Notifications: Only push to players if the weather in their zone actually changed
        if room.zone_id in shifters and room.players:
            msg = f"{Colors.CYAN}The weather shifts to {current_weather.replace('_', ' ')}.{Colors.RESET}"
            for p in room.players:
                p.send_line(msg)
        
        # [V6.0] Entity Side-Effects: Apply status effects to players/monsters in the path of the storm
        if current_weather in WEATHER_TO_STATUS:
            status_id, duration = WEATHER_TO_STATUS[current_weather]
            for entity in room.players + room.monsters:
                # Only apply if not indoors (Grammar logic)
                if getattr(room, 'terrain', '') != 'indoors':
                    effects.apply_effect(entity, status_id, duration)

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
