import random
from utilities.colors import Colors
from logic.core import combat
from logic.actions import skill_utils

def apply_assassin_opening(ctx):
    """
    Event: combat_calculate_damage
    Context: attacker, target, raw_damage
    """
    attacker = ctx.get('attacker')
    target = ctx.get('target')
    if not attacker or not target: return
    
    if getattr(attacker, 'active_class', None) == 'assassin':
        if target.hp >= target.max_hp:
            ctx['damage'] = int(ctx.get('damage', 0) * 1.5)
            if hasattr(attacker, 'send_line'):
                attacker.send_line(f"{Colors.RED}Assassin's Opening!{Colors.RESET}")

def apply_mark_damage(ctx):
    target = ctx.get('target')
    if "marked" in getattr(target, 'status_effects', {}):
        ctx['damage'] = int(ctx.get('damage', 0) * 1.20)

def apply_warrior_damage(ctx):
    attacker = ctx.get('attacker')
    if getattr(attacker, 'active_class', None) == 'warrior' and getattr(attacker, 'equipped_weapon', None):
        ctx['damage'] = int(ctx.get('damage', 0) * 1.10)

def combat_turn_extra_attacks(ctx):
    combatant = ctx.get('entity')
    target = ctx.get('target')
    
    if not hasattr(combatant, 'equipped_blessings'): return
    deck = combatant.equipped_blessings

    if target and target.hp > 0:
        extra_attacks = 0
        if "second_attack" in deck: extra_attacks += 1
        if "third_attack" in deck: extra_attacks += 1
        if "fourth_attack" in deck: extra_attacks += 1
        
        if extra_attacks > 0:
            dmg = combat.calculate_damage(combatant, target)
            for i in range(extra_attacks):
                if target.hp <= 0: break
                combatant.send_line(f"{Colors.YELLOW}You unleash a follow-up strike!{Colors.RESET}")
                skill_utils._apply_damage(combatant, target, dmg, "Auto Attack")

def dragoon_jump_mastery(ctx):
    player = ctx.get('player')
    skill = ctx.get('skill')
    if not skill or not hasattr(skill, 'identity_tags'): return
    if getattr(player, 'active_class', None) == 'dragoon':
        if "jump" in skill.identity_tags or "dive" in skill.identity_tags:
            ctx['multiplier'] = ctx.get('multiplier', 1.0) + 0.20

def apply_retribution_damage(ctx):
    target = ctx.get('target') # The Paladin (defender)
    attacker = ctx.get('attacker')
    
    if "retribution_aura" in getattr(target, 'status_effects', {}):
        if getattr(target, 'hp', 0) > 0: # Ensure they are still alive to retaliate
            dmg = 10 # Standardized base damage
            skill_utils._apply_damage(target, attacker, dmg, "Retribution")

def alchemist_flask_mastery(ctx):
    player = ctx.get('player')
    skill = ctx.get('skill')
    if not skill or not hasattr(skill, 'identity_tags'): return
    if getattr(player, 'active_class', None) == 'alchemist':
        if "alchemy" in skill.identity_tags or "flask" in skill.identity_tags:
            ctx['multiplier'] = ctx.get('multiplier', 1.0) + 0.20

def healer_passives(ctx):
    player = ctx.get('player')
    skill = ctx.get('skill')
    if not skill or not hasattr(skill, 'identity_tags'): return
    if "heal" in skill.identity_tags or "mend" in skill.identity_tags:
        cls = getattr(player, 'active_class', None)
        if cls == 'cleric': ctx['multiplier'] += 0.20
        elif cls == 'priest': ctx['multiplier'] += 0.25
        elif cls == 'white_mage': ctx['multiplier'] += 0.10

def malediction_reflection(ctx):
    attacker = ctx.get('attacker')
    if "malediction" in getattr(attacker, 'status_effects', {}):
        damage_attempt = ctx.get('damage', 0)
        backlash = max(1, int(damage_attempt * 0.20))
        from logic.core import resources
        resources.modify_resource(attacker, "hp", -backlash, source="Malediction")
        if hasattr(attacker, 'send_line'):
            attacker.send_line(f"{Colors.MAGENTA}The Malediction recoils upon you for {backlash} damage!{Colors.RESET}")

def apply_weapon_oil_damage(ctx):
    attacker = ctx.get('attacker')
    if attacker and "weapon_oil" in getattr(attacker, 'status_effects', {}):
        bonus = 15 # Standardized base bonus
        ctx['damage'] = ctx.get('damage', 0) + bonus

def samurai_iaido_mechanic(ctx):
    attacker = ctx.get('attacker')
    target = ctx.get('target')
    if attacker and getattr(attacker, 'active_class', None) == 'samurai':
        if target and target.hp >= target.max_hp:
            ctx['damage'] = int(ctx.get('damage', 0) * 1.20)


def third_eye_crit_bonus(ctx):
    attacker = ctx.get('attacker')
    if "third_eye" in getattr(attacker, 'status_effects', {}):
        ctx['is_crit'] = True

def engineer_construct_mastery(ctx):
    attacker = ctx.get('attacker')
    if attacker and getattr(attacker, 'leader', None):
        if getattr(attacker.leader, 'active_class', None) == 'engineer':
            if "construct" in getattr(attacker, 'tags', []) or "turret" in getattr(attacker, 'tags', []):
                ctx['damage'] = int(ctx['damage'] * 1.20)

def gambler_luck(ctx):
    attacker = ctx.get('attacker')
    if getattr(attacker, 'active_class', None) == 'gambler':
        chance = 15 # Standardized base chance
        if random.randint(1, 100) <= chance:
            ctx['is_crit'] = True

def beast_master_damage_bonus(ctx):
    mob = ctx.get('attacker')
    if mob and getattr(mob, 'leader', None):
        if getattr(mob.leader, 'active_class', None) == 'beast_master':
            ctx['damage'] = int(ctx['damage'] * 1.20)

def black_mage_power(ctx):
    player = ctx.get('player')
    skill = ctx.get('skill')
    if not skill or not hasattr(skill, 'identity_tags'): return
    if getattr(player, 'active_class', None) == 'black_mage':
        tags = skill.identity_tags
        if "spell" in tags or "fire" in tags or "ice" in tags or "lightning" in tags:
            ctx['multiplier'] += 0.20

def apply_haste_extra_attacks(ctx):
    """
    Event: calculate_extra_attacks
    Standardized extra hits for Haste. 
    Illusionists get 100% chance; others get 50%.
    """
    attacker = ctx.get('attacker')
    if attacker and "haste" in getattr(attacker, 'status_effects', {}):
        chance = 0.5
        # Illusionists are masters of haste logic
        if getattr(attacker, 'active_class', None) == 'illusionist':
            chance = 1.0
            
        if random.random() < chance:
            ctx['extra_attacks'] = ctx.get('extra_attacks', 0) + 1
            
            # Message Lock: Prevent spam if multi-hit burst is hasted
            current_tick = getattr(attacker.game, 'tick_count', 0)
            if getattr(attacker, '_last_haste_tick', -1) != current_tick:
                attacker._last_haste_tick = current_tick
                if hasattr(attacker, 'send_line'):
                    attacker.send_line(f"{Colors.YELLOW}You strike with blinding haste!{Colors.RESET}")
