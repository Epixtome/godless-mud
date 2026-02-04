import logging
from utilities.colors import Colors
from logic.engines import status_effects_engine
from utilities import combat_formatter
from utilities import mapper
from logic.engines import vision_engine

logger = logging.getLogger("GodlessMUD")

def check_cooldown(player, blessing, game=None):
    """Checks if the blessing is on cooldown."""
    game_ref = game if game else getattr(player, 'game', None)
    if hasattr(player, 'cooldowns') and blessing.id in player.cooldowns:
        current_tick = game_ref.tick_count if game_ref else 0
        remaining = player.cooldowns[blessing.id] - current_tick
        if remaining > 0:
            return False, f"{blessing.name} is on cooldown for {remaining}s."
    return True, "OK"

def set_cooldown(player, blessing, game=None):
    """Sets the cooldown for a blessing."""
    # Cooldown in JSON is in ticks (2s per tick) or seconds? 
    # Let's assume JSON 'cooldown' is in TICKS for game balance.
    game_ref = game if game else getattr(player, 'game', None)
    if not hasattr(player, 'cooldowns'):
        player.cooldowns = {}
    cd_ticks = blessing.requirements.get('cooldown', 0)
    if cd_ticks > 0 and game_ref:
        player.cooldowns[blessing.id] = game_ref.tick_count + cd_ticks

def check_resources(player, blessing):
    """
    Checks if player has resources. 
    For Concentration, we ALLOW overcasting, so this usually returns True 
    unless it's a hard block (like 0 stamina).
    """
    cost_data = blessing.requirements.get('cost', {})
    
    # Hard check for Stamina
    stamina_cost = cost_data.get('stamina', 0)
    if player.resources.get('stamina', 0) < stamina_cost:
        return False, "Not enough Stamina."
        
    # Concentration is flexible (Overcast allowed)
    return True, "OK"

def check_items(player, blessing):
    """Checks if player has required reagents."""
    # Placeholder for reagent logic
    return True, "OK"

def consume_resources(player, blessing):
    """
    Consumes resources and handles Overcast penalties.
    """
    cost_data = blessing.requirements.get('cost', {})
    
    # Stamina
    stamina_cost = cost_data.get('stamina', 0)
    if stamina_cost:
        player.resources['stamina'] = max(0, player.resources.get('stamina', 0) - stamina_cost)
        
    # Black Mage Passive: Spells cost 20% more
    if getattr(player, 'active_class', None) == 'black_mage':
        # Apply to stamina cost if any
        if stamina_cost > 0:
             extra_stamina = int(stamina_cost * 0.20)
             player.resources['stamina'] = max(0, player.resources.get('stamina', 0) - extra_stamina)

    # Concentration (Percentage Based)
    conc_percent = cost_data.get('concentration_percent', 0)
    if conc_percent > 0:
        # Calculate raw cost based on Max Concentration (usually 100 or 10)
        # Assuming Max Concentration is 100 for granularity
        max_conc = player.get_max_resource('concentration')
        current_conc = player.resources.get('concentration', 0)
        
        raw_cost = int(max_conc * (conc_percent / 100))
        
        # Black Mage Passive
        if getattr(player, 'active_class', None) == 'black_mage':
            raw_cost = int(raw_cost * 1.20)
        
        if current_conc >= raw_cost:
            player.resources['concentration'] -= raw_cost
        else:
            # OVERCAST!
            deficit = raw_cost - current_conc
            player.resources['concentration'] = 0
            
            # Penalty: HP Damage
            backlash = deficit * 2
            player.hp -= backlash
            if hasattr(player, 'send_line'):
                player.send_line(f"{Colors.RED}Overcast! You suffer {backlash} mental backlash damage!{Colors.RESET}")
            
            # Penalty: Debuff
            status_effects_engine.apply_effect(player, "mental_strain", 10)

def check_pacing(player, blessing):
    """
    Checks if the player has exceeded their actions per round.
    Defaults: Skills=2, Spells=1.
    Overrides: 'max_per_round' in blessing requirements.
    """
    # Safety: Initialize if missing (Hot-reload support)
    if not hasattr(player, 'round_actions'):
        player.round_actions = {'skill': 0, 'spell': 0}

    # Determine type
    action_type = 'skill' if 'skill' in blessing.identity_tags else 'spell'
    
    # Check for JSON override, otherwise use GDD defaults
    limit = blessing.requirements.get('max_per_round') # e.g. {"max_per_round": 2}
    if limit is None: # If the key doesn't exist, there is no limit.
        return True, "OK"
        
    current = player.round_actions.get(action_type, 0)
    
    if current >= limit:
        return False, f"You have already used {current}/{limit} {action_type}s this round."
        
    return True, "OK"

def consume_pacing(player, blessing):
    """Increments the action counter for this round."""
    # Safety: Initialize if missing
    if not hasattr(player, 'round_actions'):
        player.round_actions = {'skill': 0, 'spell': 0}

    action_type = 'skill' if 'skill' in blessing.identity_tags else 'spell'
    if action_type in player.round_actions:
        player.round_actions[action_type] += 1

def process_spell_effect(player, target, blessing, power, game=None):
    """Applies the spell's effect (Damage/Heal/Buff)."""
    game_ref = game if game else getattr(player, 'game', None)
    world_ref = game_ref.world if game_ref else None
    target_died = False
    msg = ""
    
    # --- Passive Bonuses ---
    bonus_mult = 1.0
    if getattr(player, 'active_class', None) and world_ref:
        cls = world_ref.classes.get(player.active_class) if hasattr(world_ref, 'classes') else None
        if cls and cls.bonuses and 'passive' in cls.bonuses:
            passive = cls.bonuses['passive']
            
            # Healing Bonuses (Priest, Cleric, White Mage)
            if "heal" in blessing.identity_tags or "mend" in blessing.identity_tags:
                if "Healing effects increased by 20%" in passive: # Cleric
                    bonus_mult += 0.20
                elif "Healing spells are 25% more effective" in passive: # Priest
                    bonus_mult += 0.25
                elif "Healing spells restore 10% more HP" in passive: # White Mage
                    bonus_mult += 0.10
            
            # Damage Bonuses (Black Mage)
            if "damage" in blessing.identity_tags or "fire" in blessing.identity_tags or "ice" in blessing.identity_tags:
                if "Spells deal 20% more damage" in passive:
                    bonus_mult += 0.20
    
    # Basic Damage/Heal Logic
    if "heal" in blessing.identity_tags or "mend" in blessing.identity_tags or "healing" in blessing.identity_tags:
        final_power = int(power * bonus_mult)
        
        if "aoe" in blessing.identity_tags:
            # AoE Logic
            targets = [p for p in player.room.players]
            # Add friendly mobs logic if needed
            count = 0
            for t in targets:
                t.hp = min(t.max_hp, t.hp + final_power)
                if hasattr(t, 'send_line') and t != player:
                    t.send_line(f"{player.name} heals you for {final_power} HP.")
                count += 1
            msg = f"You heal {count} targets for {final_power} HP."
        else:
            # Single Target
            target.hp = min(target.max_hp, target.hp + final_power)
            msg = f"You heal {target.name} for {final_power} HP."
            if hasattr(target, 'send_line') and target != player:
                target.send_line(f"{player.name} heals you for {final_power} HP.")
        
        # Secondary Effects for Healing Spells (Prism, Restoration)
        if "protection" in blessing.identity_tags:
            status_effects_engine.apply_effect(target, "magic_shield", 30)
            if hasattr(target, 'send_line'): target.send_line("You are protected by a prismatic shield.")
            
        if "cleanse" in blessing.identity_tags:
            negatives = ["poison", "curse", "blind", "silence", "slow", "weakness", "web", "net", "root"]
            if hasattr(target, 'status_effects'):
                to_remove = [eff for eff in target.status_effects if eff in negatives]
                for eff in to_remove:
                    del target.status_effects[eff]
                if to_remove and hasattr(target, 'send_line'):
                    target.send_line(f"You have been cleansed of: {', '.join(to_remove)}.")

    elif "restore" in blessing.identity_tags and "stamina" in blessing.identity_tags:
        amount = int(power * bonus_mult)
        target.resources['stamina'] = target.resources.get('stamina', 0) + amount
        msg = f"You restore {amount} stamina to {target.name}."
        if hasattr(target, 'send_line') and target != player:
            target.send_line(f"{player.name} restores {amount} of your stamina.")

    elif "tame" in blessing.identity_tags:
        # Tame logic (placeholder for now, but NO DAMAGE)
        msg = f"You attempt to tame {target.name}."
        # No damage applied
    elif "farsight" in blessing.identity_tags:
        # Farsight Logic
        direction = target # Target is the direction string
        
        # Traverse up to 10 steps in that direction to find the center
        curr = player.room
        steps = 0
        # Normalize direction for exit lookup
        from logic.common import get_reverse_direction # Just to ensure we have direction utils if needed, but exits keys are standard
        # Map short dirs to long if needed, but room.exits usually has full names or we rely on input being correct
        # Let's assume input is correct or mapped by caller.
        
        while steps < 10 and direction in curr.exits:
            next_room = curr.exits[direction]
            curr = next_room
            steps += 1
            
        # Generate Map
        # ignore_fog=True allows seeing unvisited rooms (Scouting)
        visible_grid = vision_engine.get_visible_rooms(curr, radius=10, world=world_ref, check_los=False)
        map_lines = mapper.draw_grid(visible_grid, curr, radius=10, visited_rooms=None, ignore_fog=True)
        msg = "\n".join(map_lines)
        
        # Apply Stun (Visual Trance) - 1 tick (2 seconds)
        status_effects_engine.apply_effect(player, "stun", 2)
        player.send_line(f"{Colors.CYAN}You enter a trance, projecting your mind to the {direction}...{Colors.RESET}")

    elif "cleanse" in blessing.identity_tags:
        # Purify Logic
        removed = []
        # List of negative effects to cleanse
        negatives = ["poison", "curse", "blind", "silence", "slow", "weakness", "web", "net", "root"]
        
        if hasattr(target, 'status_effects'):
            to_remove = [eff for eff in target.status_effects if eff in negatives]
            for eff in to_remove:
                del target.status_effects[eff]
                removed.append(eff)
        
        if removed:
            msg = f"You purify {target.name}, removing: {', '.join(removed)}."
            if hasattr(target, 'send_line'):
                target.send_line(f"{player.name} purifies you! ({', '.join(removed)} removed)")
        else:
            msg = f"You cast {blessing.name} on {target.name}, but they have no ailments."

    elif "line" in blessing.identity_tags:
        # Ray of Light Logic (2 Room Line)
        direction = target # Target is direction string
        current_room = player.room
        
        msg = f"You fire a {blessing.name} to the {direction}!"
        
        # Hit up to 2 rooms
        for i in range(2):
            # Hit enemies in current room (excluding caster)
            targets = [m for m in current_room.monsters] + [p for p in current_room.players if p != player]
            
            for t in targets:
                damage = int(power * bonus_mult)
                t.hp -= damage
                combat_formatter.format_damage(player.name, t.name, damage, source=blessing.name) # Just for logging/debug usually
                if hasattr(t, 'send_line'):
                    t.send_line(f"{Colors.BOLD}{Colors.WHITE}A searing beam of light strikes you for {damage} damage!{Colors.RESET}")
                if current_room == player.room:
                    if hasattr(player, 'send_line'):
                        player.send_line(f"You hit {t.name} for {damage}.")
            
            # Move to next room
            if direction in current_room.exits:
                next_room = current_room.exits[direction]
                if next_room != current_room:
                    current_room = next_room
                    current_room.broadcast(f"{Colors.BOLD}{Colors.WHITE}A beam of light shoots through the room from the {direction}!{Colors.RESET}")
                else:
                    break
            else:
                break
        
    elif "wall_of_fire" in blessing.identity_tags or blessing.id == "wall_of_fire":
        # Spawn Wall of Fire Item
        from models import Item
        wall = Item("Wall of Fire", "A roaring wall of magical flame.", value=0, flags=["hazard", "fire", "decay"])
        wall.timer = 10 # Lasts 10 ticks
        player.room.items.append(wall)
        msg = f"You conjure a {Colors.RED}Wall of Fire{Colors.RESET}!"

    elif any(tag in blessing.identity_tags for tag in ["buff", "utility", "protection", "aura", "enhancement"]):
        # Auto-apply Status Effect if ID matches
        # Check if blessing.id exists in status_effects
        if world_ref and blessing.id in world_ref.status_effects:
            duration = 60 # Default 60s
            
            # Bard Passive: Buffs last 1 extra round (assuming 1 round = 10s or just flat increase)
            if getattr(player, 'active_class', None) == 'bard':
                duration += 10
            
            # Apply
            status_effects_engine.apply_effect(target, blessing.id, duration)
            msg = f"You cast {blessing.name} on {target.name}."
            if hasattr(target, 'send_line') and target != player:
                target.send_line(f"{player.name} casts {blessing.name} on you.")
        else:
            # Fallback for unimplemented effects
            msg = f"You cast {blessing.name}. (Effect not yet implemented)"
            
    else:
        # Offensive
        # Check for AoE
        targets = []
        if "aoe" in blessing.identity_tags:
            # Hit all enemies in room
            targets = [m for m in player.room.monsters] + [p for p in player.room.players if p != player]
            if not targets:
                msg = "The spell fizzles; there are no targets here."
                return True, msg, False
            msg = f"You cast {blessing.name}, hitting {len(targets)} targets!"
        else:
            # Single Target
            targets = [target]

        for t in targets:
            # Apply damage
            damage = int(power * bonus_mult)
            
            # Apply Defense
            defense = 0
            if hasattr(t, 'get_defense'):
                defense = t.get_defense()
            elif hasattr(t, 'equipped_armor') and t.equipped_armor:
                defense = t.equipped_armor.defense
            
            damage = max(1, damage - defense)
            
            t.hp -= damage
            
            # Check if this offensive spell also has a status effect definition (e.g. frost_nova)
            if world_ref and blessing.id in world_ref.status_effects:
                # Apply effect (Default 10s / 5 ticks)
                status_effects_engine.apply_effect(t, blessing.id, 10)
            
            # Handle Stun Tag
            if "stun" in blessing.identity_tags:
                status_effects_engine.apply_effect(t, "stun", 4)
                if hasattr(t, 'send_line'): t.send_line(f"{Colors.YELLOW}You are stunned by the blast!{Colors.RESET}")
            
            att_msg, tgt_msg, _ = combat_formatter.format_damage(player.name, t.name, damage, source=blessing.name)
            if hasattr(player, 'send_line'):
                player.send_line(att_msg)
            if hasattr(t, 'send_line'):
                t.send_line(tgt_msg)
            
            if t.hp <= 0:
                target_died = True
                if hasattr(player, 'send_line'):
                    player.send_line(f"{Colors.BOLD}{Colors.YELLOW}You have defeated {t.name}!{Colors.RESET}")
                
                # Handle Death Immediately
                from models import Monster, Player
                from logic.engines import combat_processor
                if isinstance(t, Monster):
                    combat_processor.handle_mob_death(game_ref, t, player)
                elif isinstance(t, Player):
                    combat_processor.handle_player_death(game_ref, t, player)

        if not "aoe" in blessing.identity_tags:
            msg = "" # Message handled by format_damage
            
    return True, msg, target_died