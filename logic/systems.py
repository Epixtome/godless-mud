import random
from logic.engines import combat_processor
from logic import mob_manager
from utilities.colors import Colors

def auto_attack(game):
    """Heartbeat task to process one round of combat."""
    combat_processor.process_round(game)

def passive_regen(game):
    """Heartbeat task for HP regeneration."""
    for player in game.players.values():
        # HP Regen
        if player.hp < player.max_hp and not player.is_in_combat():
            regen = 1
            player.hp = min(player.max_hp, player.hp + regen)
            
        # Concentration Regen
        # Regens slowly in combat, fast out of combat
        max_conc = player.get_max_resource('concentration')
        conc_regen = 5 if player.is_in_combat() else 10
        if player.is_resting: conc_regen = 20
        
        player.resources['concentration'] = min(max_conc, player.resources.get('concentration', 0) + conc_regen)

        # Stamina Regen
        max_stamina = player.get_max_resource('stamina')
        stamina_regen = 1
        if player.is_resting: stamina_regen = 10
        
        player.resources['stamina'] = min(max_stamina, player.resources.get('stamina', 0) + stamina_regen)

    # Mob Regen & Mechanics
    for room in game.world.rooms.values():
        for mob in room.monsters:
            # Standard Regen
            if mob.hp < mob.max_hp:
                mob.hp = min(mob.max_hp, mob.hp + 1)
            
            # Resource Regen for AI
            if hasattr(mob, 'resources'):
                max_conc = 100 # Assuming mobs have a max of 100
                mob.resources['concentration'] = min(max_conc, mob.resources.get('concentration', 0) + 5)
                max_stam = 100
                mob.resources['stamina'] = min(max_stam, mob.resources.get('stamina', 0) + 5)

            # Hydra/Regenerator Logic
            if "regenerator" in mob.tags and mob.body_parts:
                for part_name, part in mob.body_parts.items():
                    max_part_hp = part.get('max_hp', 20)
                    
                    # Heal damaged parts
                    if part['hp'] < max_part_hp:
                        part['hp'] += 5
                        
                        # Regrow destroyed parts
                        if part.get('destroyed', False) and part['hp'] > 0:
                            part['destroyed'] = False
                            part['hp'] = max_part_hp # Burst heal on regrow? Or gradual? Let's do full restore.
                            room.broadcast(f"{Colors.RED}{mob.name}'s {part_name} twists and regrows in a spray of ichor!{Colors.RESET}")
                        else:
                            part['hp'] = min(max_part_hp, part['hp'])

def process_rest(game):
    """Heartbeat task to handle resting players."""
    for player in game.players.values():
        if player.is_resting:
            # Rest Regen: 10% of Max HP per tick
            regen_amount = int(player.max_hp * 0.10)
            player.hp = min(player.max_hp, player.hp + regen_amount)
            
            if game.tick_count >= player.rest_until:
                player.is_resting = False
                player.send_line(f"{Colors.GREEN}You feel rested and ready to act.{Colors.RESET}")

def reset_round_counters(game):
    """Resets action limits for the new round."""
    for player in game.players.values():
        player.round_actions = {'skill': 0, 'spell': 0}

def decay(game):
    pass

WEATHER_TABLE = {
    "default": ["clear", "cloudy", "rain"],
    "kingdom_light": ["clear", "sunny", "blinding_light"],
    "kingdom_dark": ["foggy", "dark_mist", "void_storm"],
    "kingdom_instinct": ["overcast", "rain", "thunderstorm"]
}

def weather(game):
    """Updates weather per zone."""
    # Run every 50 ticks (100 seconds)
    if game.tick_count % 50 != 0:
        return
        
    for zone in game.world.zones.values():
        # Determine weather options
        options = WEATHER_TABLE.get(zone.id, WEATHER_TABLE["default"])
        new_weather = random.choice(options)
        
        # Notify players in that zone
        # (Optimization: In a real MUD, we'd track players per zone to avoid iterating all rooms)
        for room in game.world.rooms.values():
            if room.zone_id == zone.id and room.players:
                for p in room.players:
                    p.send_line(f"{Colors.CYAN}The weather shifts to {new_weather.replace('_', ' ')}.{Colors.RESET}")

def time_of_day(game):
    """Updates global time."""
    # Cycle length: 300 ticks (10 minutes)
    # 0-75: Morning, 75-150: Day, 150-225: Evening, 225-300: Night
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