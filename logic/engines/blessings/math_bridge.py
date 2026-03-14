import logging
from utilities.utils import roll_dice
from logic.core import event_engine, effects, resources
from logic.core.systems.status import definitions
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

            if rule.get('consume'):
                _set_resource_value(player, resource_key, 0)
            
        elif r_type == 'hp_inverse' and player:
            hp_percent = player.hp / max(1, player.max_hp)
            max_bonus = rule.get('max_bonus', 2.0)
            mult *= (1.0 + (1.0 - hp_percent) * max_bonus)

        elif r_type == 'status_mod' and player:
            status_id = rule.get('status_id')
            if status_id and (effects.has_effect(player, status_id) or effects.has_effect(player, f"{status_id}_echo")):
                mult *= rule.get('multiplier', 1.0)
            
        elif r_type == 'mitigation_mod' and player:
            # Used for targets to reduce incoming damage
            status_id = rule.get('status_id')
            if status_id and effects.has_effect(player, status_id):
                # We return a reduction multiplier (e.g. 0.85 means 15% reduction)
                mult *= rule.get('multiplier', 1.0)
            
    return mult, flat

def calculate_power(blessing, player, target=None):
    """
    Calculates the final power output based on base_power and scaling tags.
    V6.0: Integrated Attacker AND Target Passive Evaluation.
    """
    base = getattr(blessing, 'base_power', 0)
    
    if base == 0:
        d_dice = getattr(blessing, 'damage_dice', None)
        if d_dice: base = roll_dice(d_dice) or 0
    
    scaling_bonus = 0
    scaling = getattr(blessing, 'scaling', [])
    if isinstance(scaling, dict): scaling = [scaling]
    
    if player and scaling:
        from logic import calibration
        for entry in scaling:
            tag = entry.get('scaling_tag')
            mult = entry.get('multiplier', 1.0)
            if tag:
                # [V6.0] Non-Linear Scaling (Diminishing Returns)
                voltage = player.get_global_tag_count(tag) if hasattr(player, 'get_global_tag_count') else 0
                
                import math
                # Curve: Reward early points, taper off at high voltage
                dr_mult = math.sqrt(voltage) * calibration.ScalingRules.DR_COEFFICIENT * mult
                
                # Breakthrough Milestone
                if voltage >= calibration.ScalingRules.BREAKTHROUGH_THRESHOLD:
                    dr_mult += calibration.ScalingRules.BREAKTHROUGH_BONUS
                    
                scaling_bonus += int(base * dr_mult) 

        # [V6.1] Elemental Payoffs (Chess-Math)
        identity = getattr(blessing, 'identity_tags', [])
        if "lightning" in identity and effects.has_effect(target, "wet"):
            scaling_bonus += base # Guaranteed 2x
        if "fire" in identity and effects.has_effect(target, "frozen"):
            scaling_bonus += base # Shatter mechanic
        if "divine" in identity and (effects.has_effect(target, "dazzled") or effects.has_effect(target, "blinded")):
            scaling_bonus += base * 1.5 # Holy Smite Payoff
        if "beast" in identity and (effects.has_effect(target, "stunned") or effects.has_effect(target, "prone")):
            scaling_bonus += base # Pack Tactics Payoff
        if "psychic" in identity and effects.has_effect(target, "confused"):
            scaling_bonus += base * 1.5 # Mind Shatter Payoff
        if "finisher" in identity and "dark" in identity:
            # Morbidity Scaling: count debuffs
            t_effects = getattr(target, 'status_effects', {})
            debuff_count = len([s for s in t_effects if s in definitions.HARD_DEBUFFS or s in definitions.SOFT_DEBUFFS])
            scaling_bonus += int(base * 0.3 * debuff_count)
        if "arcane" in identity and "red_mage" in identity and effects.has_effect(player, "dualcast"):
             scaling_bonus += base # Guaranteed 2x for Dualcast
    
    total = base + scaling_bonus
    
    # 1. Active Blessing Rules
    dyn_mult, dyn_flat = process_potency_modifiers(blessing, player, target)
    
    # 2. Attacker-Side Passives
    if player and hasattr(player, 'equipped_blessings'):
        for b_id in player.equipped_blessings:
            if b_id == blessing.id: continue
            pass_blessing = player.game.world.blessings.get(b_id) if hasattr(player, 'game') else None
            if pass_blessing and getattr(pass_blessing, 'logic_type', None) == 'passive':
                p_mult, p_flat = process_potency_modifiers(pass_blessing, player, target)
                dyn_mult *= p_mult
                dyn_flat += p_flat

    # 3. Target-Side Passives (Mitigation/Defense)
    if target and hasattr(target, 'equipped_blessings'):
        for b_id in target.equipped_blessings:
            pass_blessing = target.game.world.blessings.get(b_id) if hasattr(target, 'game') else None
            if pass_blessing and getattr(pass_blessing, 'logic_type', None) == 'passive':
                # Target passives use process_potency_modifiers with r_type 'mitigation_mod'
                t_mult, _ = process_potency_modifiers(pass_blessing, target, player) # target is 'at' player here
                dyn_mult *= t_mult # Reduction applies directly to total power

    total = (total * dyn_mult) + dyn_flat

    # Dispatch Modifier Event (For remaining legacy module logic)
    ctx = {'attacker': player, 'blessing': blessing, 'target': target, 'multiplier': 1.0, 'bonus_flat': 0, 'power': total}
    event_engine.dispatch("calculate_damage_modifier", ctx)
    
    total = int(ctx['power'] * ctx['multiplier']) + ctx['bonus_flat']
    return max(1, total)

def apply_on_hit(player, target, blessing=None):
    """Applies on_hit effects defined in JSON and Gear flags."""
    if getattr(player, 'suppress_on_hit', False): return

    # 1. Blessing-Specific On-Hit (If active skill used)
    if blessing:
        on_hit = getattr(blessing, 'on_hit', None)
        if on_hit and isinstance(on_hit, dict):
            status = on_hit.get('apply_status')
            if status:
                duration = on_hit.get('duration', 10)
                is_refresh = effects.has_effect(target, status)
                effects.apply_effect(target, status, duration)
                if not is_refresh and hasattr(target, 'room') and target.room:
                    target.room.broadcast(f"{Colors.YELLOW}{target.name} is knocked {status.replace('_', ' ').title()}!{Colors.RESET}", exclude_player=None)

            bal_dmg = on_hit.get('balance_damage')
            if bal_dmg and target:
                from logic.core.utils import combat_logic
                b_tags = set(getattr(blessing, 'identity_tags', []))
                combat_logic.check_posture_break(target, bal_dmg, source=player, tags=b_tags)

            if on_hit.get('interrupt') and target:
                if hasattr(target, 'current_action') and target.current_action:
                    target.current_action = None
                    if hasattr(target, 'send_line'): target.send_line(f"{Colors.RED}Your concentration is SHATTERED! Action interrupted.{Colors.RESET}")

        # 1b. Passive Blessing List Effects (Legacy/V2)
        effect_list = getattr(blessing, 'effects', [])
        if effect_list:
            for effect in effect_list:
                eff_id = effect.get('id')
                duration = effect.get('duration', 4)
                tgt_type = effect.get('target', 'enemy')
                if tgt_type == 'enemy' and target: effects.apply_effect(target, eff_id, duration)
                elif tgt_type == 'self' and player: effects.apply_effect(player, eff_id, duration)

    # 2. Universal Tactical Hooks (Deterministic RPS)
    if hasattr(player, 'equipped_weapon') and player.equipped_weapon:
        w = player.equipped_weapon
        w_flags = getattr(w, 'flags', [])
        w_tags = getattr(w, 'tags', [])
        
        # Bleed/Poison (100% Effective on Hit)
        if "bleed" in w_flags or "bleed" in w_tags:
            effects.apply_effect(target, "bleed", 10)
        if "poison" in w_flags or "poison" in w_tags:
            effects.apply_effect(target, "poison", 10)
            
        # [V6.0] Deterministic Interactions (NO RNG)
        # Weight vs Off-Balance = Prone
        if ("weight" in w_tags or "weight" in w_flags) and effects.has_effect(target, "off_balance"):
            effects.apply_effect(target, "prone", 4)
            if hasattr(player, 'send_line'):
                player.send_line(f"{Colors.YELLOW}The weight of your {w.name} crushes the unsteady {target.name} to the ground!{Colors.RESET}")

        # Precision vs Exposed
        if "precision" in w_tags and effects.has_effect(target, "stun"):
            # Guaranteed critical location hit (Example logic)
            pass
            
        # elemental damage when wet
        if "elemental" in (getattr(blessing, 'identity_tags', []) if blessing else []) and effects.has_effect(target, "wet"):
             # This would be handled in damage calc, but we can log it here
             pass

def calculate_duration(blessing, player):
    if hasattr(blessing, 'metadata') and blessing.metadata:
        return blessing.metadata.get('duration', 30)
    return 30

def calculate_weapon_power(weapon, player, avg=False):
    """
    Calculates weapon damage with V6.0 scaling and resonance.
    Pillar: Physics should live in Data (Weapons/Stats).
    """
    from logic import calibration
    
    # 1. Base Harvest
    stats = getattr(weapon, 'stats', {})
    damage_dice = stats.get('damage_dice') or getattr(weapon, 'damage_dice', "1d4")
    
    if avg:
        try:
            dice_count, dice_sides = map(int, damage_dice.split('d'))
            base = dice_count * (dice_sides + 1) / 2
        except (ValueError, AttributeError, TypeError): base = 1
    else:
        base = roll_dice(damage_dice) or 1
        
    # 2. Voltage Scaling (Tag Synergy)
    # Priority: stats.scaling_tag -> weapon.scaling_tag -> legacy scaling dict
    scaling_tag = stats.get('scaling_tag') or getattr(weapon, 'scaling_tag', 'martial')
    scaling_mult = stats.get('scaling_mult') or getattr(weapon, 'scaling_mult', 1.0)
    
    # Fallback to legacy scaling format if needed
    if not stats.get('scaling_tag'):
        legacy = getattr(weapon, 'scaling', {})
        if isinstance(legacy, dict) and 'tag' in legacy:
            scaling_tag = legacy.get('tag', scaling_tag)
            scaling_mult = legacy.get('mult', scaling_mult)
            
    voltage = player.get_global_tag_count(scaling_tag) if player and hasattr(player, 'get_global_tag_count') else 0
    
    import math
    # [V6.0] Non-Linear Scaling
    dr_mult = math.sqrt(voltage) * calibration.ScalingRules.DR_COEFFICIENT * scaling_mult
    
    # Breakthrough Milestone
    if voltage >= calibration.ScalingRules.BREAKTHROUGH_THRESHOLD:
        dr_mult += calibration.ScalingRules.BREAKTHROUGH_BONUS
        
    power_mult = 1.0 + dr_mult
    
    total = int(base * power_mult)
    
    # 3. Resonance Bonus (Flat Thresholds)
    resonance = getattr(weapon, 'resonance', {})
    if resonance and player and hasattr(player, 'get_global_tag_count'):
        r_tag = resonance.get('tag')
        r_thresh = resonance.get('threshold', 0)
        if r_tag and player.get_global_tag_count(r_tag) >= r_thresh:
            total += resonance.get('bonus_dmg', 0)
                
    return max(1, total)

def resolve_reaction(attacker, target, attack_tags):
    """
    [V6.0] Evaluates if a defender's active reaction (Parry/Block) succeeds.
    Returns: (bool success, str feedback_message, dict result_mods)
    """
    # 1. Check for active Reaction Statuses
    t_effects = getattr(target, 'status_effects', {})
    if not t_effects: return False, "", {}

    from logic.core.utils import combat_logic
    a_weight = combat_logic.get_weight_class(attacker)
    t_weight = combat_logic.get_weight_class(target)
    
    # --- MONK: FLOW PARRY (Light/Speed) ---
    if "flow_mastery" in t_effects:
        # Counter-Tags: Cannot parry mass or sweeps
        if "weight" in attack_tags or "sweep" in attack_tags:
            return False, f"The weight of {attacker.name}'s strike is too great to parry!", {}
            
        # Physics: Heavy weapons are harder to parry with light flow
        if a_weight == "heavy" and t_weight == "light":
             return False, f"{attacker.name}'s momentum overpowers your flow!", {}

        # Success: Deterministic Dodge + Riposte
        effects.apply_effect(target, "riposte_ready", 2)
        effects.apply_effect(attacker, "staggered", 4)
        return True, "You flow around the strike, readying a counter!", {"power_mult": 0}

    # --- KNIGHT: BULWARK (Heavy/Shield) ---
    if "ready_bulwark" in t_effects:
        # Counter-Tags: Hammers/Blunt skip the shield parry
        if "blunt" in attack_tags or "shield_breaker" in attack_tags:
            return False, f"{attacker.name}'s blow shatters through your guard!", {}

        # Success: Hard Block + Off-Balance
        effects.apply_effect(target, "riposte_ready", 2)
        effects.apply_effect(attacker, "off_balance", 4)
        return True, "You catch the strike on your shield, forcing them open!", {"power_mult": 0}

    # --- BARBARIAN: BLOOD COUNTER (Medium/Fury) ---
    if "blood_counter_ready" in t_effects:
        # Physics: Cannot counter if completely incapacitated
        if "stun" in t_effects or "prone" in t_effects:
             return False, "", {}

        # Success: Take 50% damage, deal free hit.
        effects.remove_effect(target, "blood_counter_ready")
        return True, "You take the blow and strike back with fury!", {"power_mult": 0.5, "counter_strike": True}

    # --- MAGE: PHASE SHIFT (Arcane/Glass) ---
    if "phase_shifted" in t_effects:
        # Counter-Tags: Cannot phase through arcane/void logic
        if "arcane" in attack_tags or "void" in attack_tags or "magic" in attack_tags:
             return False, "The arcane nature of the strike anchors you to reality!", {}
        
        # Success: Complete negations of physical matter
        return True, "You phase through the physical strike!", {"power_mult": 0}

    # --- WARLOCK: ELDRITCH WARD (Entropy/Void) ---
    if "eldritch_ward_ready" in t_effects:
        # Success: Negate hit, refund concentration (Void Siphon)
        resources.modify_resource(target, "concentration", 15, source="Void Ward")
        effects.remove_effect(target, "eldritch_ward_ready")
        return True, "The void swallows the strike and feeds your mind!", {"power_mult": 0}

    # --- ASSASSIN: SMOKE SCREEN (Light/Stealth) ---
    if "smoke_screen" in t_effects:
        # Counter-Tags: Cannot hide from senses like [Detection] or [True Sight]
        if "detection" in attack_tags or "true_sight" in attack_tags:
            return False, "The attacker sees right through the smoke!", {}
            
        # Success: Complete negation + Chance to vanish
        effects.apply_effect(target, "concealed", 3)
        return True, "You vanish into the smoke as the strike passes through thin air!", {"power_mult": 0}

    # --- CLERIC: DIVINE GRACE (Divine/Favor) ---
    if "divine_grace_ready" in t_effects:
        # Success: Negate hit, Restore 20 Concentration
        resources.modify_resource(target, "concentration", 20, source="Divine Grace")
        effects.remove_effect(target, "divine_grace_ready")
        return True, "A shimmer of divine light intercepts the blow!", {"power_mult": 0}

    # --- BEASTMASTER: BESTIAL REFLEX (Beast/Bond) ---
    if "bestial_bond_active" in t_effects:
        # Success: Pet intercepts. For now, we just negate Master's damage.
        # Future: Transfer % to Pet entity.
        effects.remove_effect(target, "bestial_bond_active")
        return True, "Your pet leaps in front of the strike, guarding you!", {"power_mult": 0}

    # --- ILLUSIONIST: MIRROR IMAGE (Illusion/Trick) ---
    if "mirror_image_active" in t_effects:
        # Success: Strike hits decoy. Confuse attacker.
        effects.apply_effect(attacker, "confused", 4)
        effects.remove_effect(target, "mirror_image_active")
        return True, "Your image shatters into light, leaving the attacker dazed!", {"power_mult": 0}

    # --- DEFILER: BLOOD VEIL (Dark/Ichor) ---
    if "blood_veil_active" in t_effects:
        # Success: Take 50% damage, Attacker gets Malediction
        effects.apply_effect(attacker, "malediction", 6)
        effects.remove_effect(target, "blood_veil_active")
        return True, "Blood mist absorbs the strike, weaving a curse around the attacker!", {"power_mult": 0.5}

    # --- RED MAGE: FENCER'S WARD (Rapier/Weave) ---
    if "fencers_ward_active" in t_effects:
        # Success: Parry hit, grant Dualcast
        effects.apply_effect(target, "dualcast", 5)
        effects.remove_effect(target, "fencers_ward_active")
        return True, "You parry the strike with fluid grace, charging your next spell!", {"power_mult": 0}

    return False, "", {}

def resolve_blessing_effect(player, blessing):
    return calculate_power(blessing, player)

class MathBridge:
    """Legacy shim."""
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
