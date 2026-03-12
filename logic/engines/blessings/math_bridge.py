import logging
from utilities.utils import roll_dice
from logic.core import event_engine
from logic.core import effects
from utilities.colors import Colors
from logic.constants import Tags

logger = logging.getLogger("GodlessMUD")

def _get_resource_value(player, key):
    """Helper to traverse player state for resources (e.g. 'monk.flow_pips')."""
    if not player or not key: return 0
    parts = key.split('.')
    if len(parts) == 2:
        return player.ext_state.get(parts[0], {}).get(parts[1], 0)
    return 0

def _set_resource_value(player, key, value):
    """Helper to set player state resources (e.g. resetting 'barbarian.momentum')."""
    if not player or not key: return
    parts = key.split('.')
    if len(parts) == 2:
        player.ext_state.setdefault(parts[0], {})[parts[1]] = value

def process_potency_modifiers(blessing, player, target=None):
    """
    Evaluates complex scaling rules defined in JSON shards.
    Pillar 6: Physics and Math should live in Data, not Logic.
    """
    mult = 1.0
    flat = 0
    rules = getattr(blessing, 'potency_rules', [])
    if not isinstance(rules, list):
        # Handle single rule dict
        rules = [rules] if isinstance(rules, dict) else []

    for rule in rules:
        r_type = rule.get('type')
        if r_type == 'pip_scaling' and player:
            resource_key = rule.get('resource') 
            pips = _get_resource_value(player, resource_key)
            
            tiers = rule.get('tiers', [])
            matched_tier = None
            for tier in tiers:
                if pips <= tier.get('max', 999):
                    matched_tier = tier
                    break
            
            if matched_tier:
                base = matched_tier.get('base', 1.0)
                per = matched_tier.get('mult_per', 0)
                offset = matched_tier.get('offset', 0)
                mult *= (base + (pips - offset) * per)
            
            flat += pips * rule.get('flat_per', 0)

            # [V5.3] Consumption Support (e.g. Barbarian Momentum expense)
            if rule.get('consume'):
                _set_resource_value(player, resource_key, 0)
            
        elif r_type == 'hp_inverse' and player:
            # Desperation Scaling (Warlock)
            hp_percent = player.hp / max(1, player.max_hp)
            max_bonus = rule.get('max_bonus', 2.0)
            mult *= (1.0 + (1.0 - hp_percent) * max_bonus)

        elif r_type == 'status_mod' and player:
            # Conditional multiplier based on status presence
            status_id = rule.get('status_id')
            if status_id and (effects.has_effect(player, status_id) or effects.has_effect(player, f"{status_id}_echo")):
                mult *= rule.get('multiplier', 1.0)
            
    return mult, flat

def calculate_power(blessing, player, target=None):
    """
    Calculates the final power output based on base_power and scaling tags.
    V5.1: Integrated Dynamic Potency Rules from JSON.
    """
    base = getattr(blessing, 'base_power', 0)
    
    # [V1] Legacy Scaling Logic (Tag Synergy)
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
    
    # [V5.1] Dynamic Potency Rules (Current Action)
    dyn_mult, dyn_flat = process_potency_modifiers(blessing, player, target)
    
    # [V5.2] Global Passives (Equipped Blessings of type 'passive')
    if player and hasattr(player, 'game') and player.game:
        # We look at equipped blessings to find passives with potency rules
        for b_id in getattr(player, 'equipped_blessings', []):
            if b_id == blessing.id: continue # Don't double-process if action itself is passive
            
            pass_blessing = player.game.world.blessings.get(b_id)
            if pass_blessing and getattr(pass_blessing, 'logic_type', None) == 'passive':
                p_mult, p_flat = process_potency_modifiers(pass_blessing, player, target)
                dyn_mult *= p_mult
                dyn_flat += p_flat

    total = (total * dyn_mult) + dyn_flat

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
            effects.apply_effect(target, status, duration)
            # Broadcast the Opening
            if hasattr(target, 'room') and target.room:
                target.room.broadcast(f"{Colors.YELLOW}{target.name} is knocked {status.replace('_', ' ').title()}!{Colors.RESET}", exclude_player=None)

    # Apply V2 Effects List (MVP)
    effect_list = getattr(blessing, 'effects', [])
    if effect_list:
        for effect in effect_list:
            eff_id = effect.get('id')
            duration = effect.get('duration', 4)
            tgt_type = effect.get('target', 'enemy')
            
            if tgt_type == 'enemy' and target:
                effects.apply_effect(target, eff_id, duration)
            elif tgt_type == 'self' and player:
                effects.apply_effect(player, eff_id, duration)

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
