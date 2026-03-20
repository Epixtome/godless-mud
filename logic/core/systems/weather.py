import os
import json
import random
import logging
from utilities.colors import Colors
from logic.core import effects, event_engine

logger = logging.getLogger("GodlessMUD")

# V6.3: Weather Registry
WEATHER_CONFIG = None

def _load_config():
    path = "data/systems/weather.json"
    if not os.path.exists(path):
         return {}
    try:
         with open(path, 'r', encoding='utf-8') as f:
              return json.load(f)
    except Exception as e:
         logger.error(f"Error loading weather config: {e}")
         return {}

def get_weather_config():
    global WEATHER_CONFIG
    if WEATHER_CONFIG is None:
        WEATHER_CONFIG = _load_config()
    return WEATHER_CONFIG

def update_room_environmental_state(room, game):
    """
    [V6.3] Synchronizes a room's terrain and grammar with the zone-wide weather.
    Recommended for call on: Entity Entry, System Heartbeat.
    """
    config = get_weather_config()
    if not config: return
    
    current_weather = game.world.zone_weather.get(room.zone_id, "clear")
    room.apply_weather_effect(current_weather, config)
    
    # Optional: Apply initial status effects to entering entity? 
    # Usually handled by the main heartbeat or a specific entry listener.

def weather_pulse(game):
    """
    [V6.3] Advanced Weather Engine.
    Coordinates zone-wide shifts and room-wide terrain/grammar transitions.
    """
    global WEATHER_CONFIG
    if WEATHER_CONFIG is None:
        WEATHER_CONFIG = _load_config()
        
    if game.tick_count % 50 != 0:
        return
        
    # 1. Zone-wide Shifters (Macro-scale Persistence)
    zones_to_push = []
    weather_zones = WEATHER_CONFIG.get("weather_zones", {})
    transitions = WEATHER_CONFIG.get("transitions", {})
    
    for zone_id in game.world.zones:
        old_weather = game.world.zone_weather.get(zone_id, "clear")
        
        # Use transition table for realism, or random choice as fallback
        if old_weather in transitions:
            choices = transitions[old_weather]
            # Probabilistic pick
            r = random.random()
            cumulative = 0
            new_weather = old_weather # Fallback
            for opt, prob in choices.items():
                cumulative += prob
                if r <= cumulative:
                    new_weather = opt
                    break
        else:
            options = weather_zones.get(zone_id, weather_zones.get("default", ["clear"]))
            new_weather = random.choice(options)
            
        if new_weather != old_weather:
            game.world.zone_weather[zone_id] = new_weather
            zones_to_push.append(zone_id)
            
    # 2. Room-wide Synchronization (Active Only)
    weather_to_status = WEATHER_CONFIG.get("weather_to_status", {})
    for room in list(game.world.active_rooms):
        current_weather = game.world.zone_weather.get(room.zone_id, "clear")
        
        # Terrain Shifting (Grammar Interaction)
        room.apply_weather_effect(current_weather, WEATHER_CONFIG)
        
        # Player Notifications
        if room.zone_id in zones_to_push and room.players:
            msg = f"{Colors.CYAN}The environment shifts: {current_weather.replace('_', ' ')}.{Colors.RESET}"
            for p in room.players:
                p.send_line(msg)
        
        # Status Effect Distribution (V6.4: Silent Refresh for Mass-Applied Weather)
        if current_weather in weather_to_status and room.terrain != 'indoors':
            status_id, duration = weather_to_status[current_weather]
            for entity in room.players + room.monsters:
                 # [V6.4] Avoid Spam: Only re-apply if the effect is missing or about to expire (< 5s)
                 expiry = getattr(entity, 'status_effects', {}).get(status_id, 0)
                 if expiry - game.tick_count < 5:
                      effects.apply_effect(entity, status_id, duration, log_event=False)

def on_calculate_damage(ctx):
    """
    [V6.3] Grammar Listener: Applies weather-based damage multipliers.
    Driven by 'payoffs' in weather.json.
    """
    attacker = ctx.get('attacker')
    tags = ctx.get('tags', set())
    if not attacker: return
    
    room = getattr(attacker, 'room', None)
    if not room: return
    
    config = get_weather_config()
    current_weather = room.get_weather()
    
    # 1. Weather-Specific Payoffs
    payoffs = config.get("payoffs", {}).get(current_weather, {})
    for tag in tags:
        if tag in payoffs:
            ctx['multiplier'] *= payoffs[tag]

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


# --- Event Subscriptions ---
event_engine.subscribe("calculate_damage_modifier", on_calculate_damage)
