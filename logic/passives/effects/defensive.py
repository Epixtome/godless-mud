import random
from utilities.colors import Colors

# Configuration
CONSTANTS = {
    "rogue_dodge": 0.10,
    "ninja_dodge": 0.15,
    "parry_chance": 0.50,
    "paladin_mitigation": 0.90, # 10% reduction
    "knight_mitigation": 0.95,  # 5% reduction
    "shield_faith_mitigation": 0.85,
    "magic_shield_mitigation": 0.80,
    "sanctify_mitigation": 0.90,
    "infused_gear_mitigation": 0.85
}

def apply_evasive_step(ctx):
    """
    Event: combat_check_dodge
    Context: attacker, target, dodged (bool)
    """
    defender = ctx.get('target')
    if not defender: return

    if "evasive_step" in getattr(defender, 'status_effects', {}):
        bonus = 30 # Standardized base bonus
        
        if not ctx.get('dodged'):
            if random.randint(1, 100) <= bonus:
                ctx['dodged'] = True
                if hasattr(defender, 'resources'):
                    defender.resources['stamina'] = max(0, defender.resources.get('stamina', 0) - 1)
                if hasattr(defender, 'send_line'):
                    defender.send_line(f"{Colors.CYAN}You evade the attack with a quick step!{Colors.RESET}")

def apply_rogue_dodge(ctx):
    defender = ctx.get('target')
    if getattr(defender, 'active_class', None) == 'rogue':
        if random.random() < CONSTANTS["rogue_dodge"]:
            ctx['dodged'] = True

def apply_ninja_dodge(ctx):
    defender = ctx.get('target')
    if getattr(defender, 'active_class', None) == 'ninja':
        if random.random() < CONSTANTS["ninja_dodge"]:
            ctx['dodged'] = True

def apply_parry(ctx):
    defender = ctx.get('target')
    if "parrying" in getattr(defender, 'status_effects', {}):
        if random.random() < CONSTANTS["parry_chance"]:
            ctx['dodged'] = True
            if hasattr(defender, 'send_line'):
                defender.send_line(f"{Colors.CYAN}You parry the attack!{Colors.RESET}")

def apply_class_defense(ctx):
    """Handles Paladin and Knight damage reduction."""
    target = ctx.get('target')
    cls = getattr(target, 'active_class', None)
    damage = ctx.get('damage', 0)
    
    if cls == 'paladin':
        ctx['damage'] = int(damage * CONSTANTS["paladin_mitigation"])
    elif cls == 'knight':
        ctx['damage'] = int(damage * CONSTANTS["knight_mitigation"])

def apply_buff_mitigation(ctx):
    """Handles mitigation from buffs like Magic Shield, Sanctify, etc."""
    target = ctx.get('target')
    effects = getattr(target, 'status_effects', {})
    damage = ctx.get('damage', 0)
    
    # Magic Shield (Spells only)
    if "magic_shield" in effects and ctx.get('type') == 'skill':
        damage = int(damage * CONSTANTS["magic_shield_mitigation"])
        
    if "sanctified" in effects:
        damage = int(damage * CONSTANTS["sanctify_mitigation"])
        
    if "shield_of_faith" in effects:
        damage = int(damage * CONSTANTS["shield_faith_mitigation"])
        
    if "infused_gear" in effects:
        damage = int(damage * CONSTANTS["infused_gear_mitigation"])
        
    ctx['damage'] = damage