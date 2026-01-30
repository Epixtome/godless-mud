import logging
from utilities.colors import Colors
from logic.engines import status_effects_engine
from utilities import combat_formatter
from logic import mapper

logger = logging.getLogger("GodlessMUD")

def check_cooldown(player, blessing):
    """Checks if the blessing is on cooldown."""
    if blessing.id in player.cooldowns:
        remaining = player.cooldowns[blessing.id] - player.game.tick_count
        if remaining > 0:
            return False, f"{blessing.name} is on cooldown for {remaining}s."
    return True, "OK"

def set_cooldown(player, blessing):
    """Sets the cooldown for a blessing."""
    # Cooldown in JSON is in ticks (2s per tick) or seconds? 
    # Let's assume JSON 'cooldown' is in TICKS for game balance.
    cd_ticks = blessing.requirements.get('cooldown', 0)
    if cd_ticks > 0:
        player.cooldowns[blessing.id] = player.game.tick_count + cd_ticks

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

    # Concentration (Percentage Based)
    conc_percent = cost_data.get('concentration_percent', 0)
    if conc_percent > 0:
        # Calculate raw cost based on Max Concentration (usually 100 or 10)
        # Assuming Max Concentration is 100 for granularity
        max_conc = 100 
        current_conc = player.resources.get('concentration', 0)
        
        raw_cost = int(max_conc * (conc_percent / 100))
        
        if current_conc >= raw_cost:
            player.resources['concentration'] -= raw_cost
        else:
            # OVERCAST!
            deficit = raw_cost - current_conc
            player.resources['concentration'] = 0
            
            # Penalty: HP Damage
            backlash = deficit * 2
            player.hp -= backlash
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

def process_spell_effect(player, target, blessing, power):
    """Applies the spell's effect (Damage/Heal/Buff)."""
    target_died = False
    msg = ""
    
    # Special Logic: Backstab
    if blessing.id == "backstab":
        # Requirement: Player not fighting target directly (or hidden)
        # Requirement: Target is fighting someone else (distracted)
        if player.fighting == target:
            return False, "You cannot backstab a target that is focused on you!", False
            
        if not target.fighting:
            return False, "The target is wary. Wait for them to be distracted.", False
            
        # Weapon Check
        multiplier = 1.5
        if player.equipped_weapon:
            w_name = player.equipped_weapon.name.lower()
            if "dagger" in w_name or "knife" in w_name or "blade" in w_name:
                multiplier = 5.0
        
        power = int(power * multiplier)
        msg = f"{Colors.RED}BACKSTAB!{Colors.RESET} "
        # Consume extra stamina handled by consume_resources if configured, or here manually?
        # JSON config handles base cost.

    # Basic Damage/Heal Logic
    if "heal" in blessing.identity_tags or "mend" in blessing.identity_tags:
        target.hp = min(target.max_hp, target.hp + power)
        msg = f"You heal {target.name} for {power} HP."
        if hasattr(target, 'send_line'):
            target.send_line(f"{player.name} heals you for {power} HP.")
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
        map_lines = mapper.get_large_map(player, radius=10, center_room=curr, show_entities=True, ignore_fog=True)
        msg = "\n".join(map_lines)
        
        # Apply Stun (Visual Trance) - 1 tick (2 seconds)
        status_effects_engine.apply_effect(player, "stun", 2)
        player.send_line(f"{Colors.CYAN}You enter a trance, projecting your mind to the {direction}...{Colors.RESET}")
        
    elif any(tag in blessing.identity_tags for tag in ["buff", "utility", "passive", "protection", "aura", "enhancement"]):
        # Non-damaging spells (Buffs/Utility)
        msg = f"You cast {blessing.name}."
    else:
        # Offensive
        # Apply damage
        damage = power
        # TODO: Apply resistance/defense here
        
        target.hp -= damage
        
        att_msg, tgt_msg, _ = combat_formatter.format_damage(player.name, target.name, damage, source=blessing.name)
        msg += att_msg
        if hasattr(target, 'send_line'):
            target.send_line(tgt_msg)
        
        if target.hp <= 0:
            target_died = True
            
    return True, msg, target_died