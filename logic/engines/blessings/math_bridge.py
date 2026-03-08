import logging
from utilities.utils import roll_dice
from logic.core import event_engine
from logic.core import status_effects_engine
from utilities.colors import Colors
from logic.constants import Tags

logger = logging.getLogger("GodlessMUD")

def calculate_power(blessing, player, target=None):
    """
    Calculates the final power output based on base_power and scaling tags.
    Power = Base + (Voltage * Multiplier)
    """
    base = getattr(blessing, 'base_power', 0)
    
    # Scaling Logic (Tag Synergy)
    scaling_bonus = 0
    scaling = getattr(blessing, 'scaling', [])
    if isinstance(scaling, dict): scaling = [scaling]
    
    if player and scaling:
        for entry in scaling:
            tag = entry.get('scaling_tag')
            mult = entry.get('multiplier', 1.0)
            if tag:
                voltage = player.get_global_tag_count(tag) if hasattr(player, 'get_global_tag_count') else 0
                scaling_bonus += int(voltage * mult)
    
    total = base + scaling_bonus
    
    # Dispatch Modifier Event (Decoupled Logic)
    ctx = {'attacker': player, 'blessing': blessing, 'target': target, 'multiplier': 1.0, 'bonus_flat': 0, 'power': total}
    event_engine.dispatch("calculate_damage_modifier", ctx)
    
    total = int(ctx['power'] * ctx['multiplier']) + ctx['bonus_flat']
    return max(1, total)

def apply_on_hit(player, target, blessing):
    """Applies on_hit effects defined in JSON."""
    on_hit = getattr(blessing, 'on_hit', None)
    if on_hit and isinstance(on_hit, dict):
        # Apply Status
        status = on_hit.get('apply_status')
        if status:
            duration = on_hit.get('duration', 10)
            status_effects_engine.apply_effect(target, status, duration)
            # Broadcast the Opening
            if hasattr(target, 'room') and target.room:
                target.room.broadcast(f"{Colors.YELLOW}{target.name} is knocked {status.replace('_', ' ').title()}!{Colors.RESET}", exclude_player=None)

    # Apply V2 Effects List (MVP)
    effects = getattr(blessing, 'effects', [])
    if effects:
        for effect in effects:
            eff_id = effect.get('id')
            duration = effect.get('duration', 4)
            tgt_type = effect.get('target', 'enemy')
            
            if tgt_type == 'enemy' and target:
                status_effects_engine.apply_effect(target, eff_id, duration)
            elif tgt_type == 'self' and player:
                status_effects_engine.apply_effect(player, eff_id, duration)

def calculate_duration(blessing, player):
    """Calculates duration (Simplified)."""
    if hasattr(blessing, 'metadata') and blessing.metadata:
        return blessing.metadata.get('duration', 30)
    return 30

def calculate_weapon_power(weapon, player, avg=False):
    """Calculates weapon damage (Simplified)."""
    damage_dice = getattr(weapon, 'damage_dice', None)
    if not damage_dice and hasattr(weapon, 'stats'):
        damage_dice = weapon.stats.get('damage_dice')

    if not damage_dice:
        base = 1
    elif avg:
        try:
            dice_count, dice_sides = map(int, damage_dice.split('d'))
            base = dice_count * (dice_sides + 1) / 2
        except (ValueError, AttributeError):
            base = 1
    else:
        base = roll_dice(damage_dice) or 1
    return int(base)

def resolve_blessing_effect(player, blessing):
    """
    Calculates the final effect value (damage/healing) for a blessing.
    Uses simplified Blueprint Pattern.
    """
    return calculate_power(blessing, player)

def process_red_mage_mechanics(player, blessing):
    """
    Handles Crimson Charge consumption and penalties for Red Mages.
    Called by magic_engine.consume_resources.
    """
    if not player.synergies.get('red_mage'):
        return

    is_spell = any(t in blessing.identity_tags for t in [Tags.MAGIC, Tags.ELEMENTAL, Tags.ARCANE, Tags.HOLY, Tags.DARK, Tags.SORCERY])
    is_martial = Tags.MARTIAL in blessing.identity_tags

    if is_spell and not is_martial:
        if player.crimson_charges > 0:
            player.crimson_charges -= 1
            player.send_line(f"{Colors.RED}[SYNERGY] Crimson Charge consumed! Instant Cast! (+20% Potency){Colors.RESET}")
        else:
            # Cold Mana Penalty
            player.send_line(f"{Colors.YELLOW}Your mana is cold! The spell resists your call...{Colors.RESET}")
            # Apply a synthetic cooldown delay if one doesn't exist or extend it
            if hasattr(player, 'cooldowns'):
                current_cd = player.cooldowns.get(blessing.id, player.game.tick_count)
                player.cooldowns[blessing.id] = max(current_cd, player.game.tick_count + 2) # +2 Ticks (4s) delay

class MathBridge:
    """
    Legacy shim to prevent ImportErrors in modules that haven't been refactored yet.
    """
    @staticmethod
    def calculate_power(blessing, player, target=None):
        return calculate_power(blessing, player, target)

    @staticmethod
    def calculate_weapon_power(weapon, player, avg=False):
        return calculate_weapon_power(weapon, player, avg)

    @staticmethod
    def apply_on_hit(player, target, blessing):
        return apply_on_hit(player, target, blessing)

    @staticmethod
    def calculate_duration(blessing, player):
        return calculate_duration(blessing, player)