def apply_mana_reduction(ctx):
    """
    Event: magic_calculate_cost
    """
    pass

def apply_berserker_momentum(ctx):
    target = ctx.get('target')
    if getattr(target, 'active_class', None) == 'berserker':
        if 'momentum' in target.resources:
            target.resources['momentum'] = min(100, target.resources.get('momentum', 0) + 5)

def combat_turn_momentum(ctx):
    combatant = ctx.get('entity')
    target = ctx.get('target')
    
    if not hasattr(combatant, 'equipped_blessings'): return
    deck = combatant.equipped_blessings
    
    if "whirlwind" in deck or getattr(combatant, 'active_class', None) == 'barbarian':
        is_tanking = target and target.fighting == combatant
        if is_tanking:
            current = combatant.resources.get('momentum', 0)
            combatant.resources['momentum'] = min(10, current + 1)

def monk_stance_on_hit(ctx):
    attacker = ctx.get('attacker')
    target = ctx.get('target')
    
    if attacker and "tiger_stance" in getattr(attacker, 'status_effects', {}):
        if not getattr(attacker, 'equipped_weapon', None):
            attacker.resources['chi'] = min(5, attacker.resources.get('chi', 0) + 1)

    if target and "turtle_stance" in getattr(target, 'status_effects', {}):
        if not getattr(target, 'equipped_weapon', None):
            target.resources['chi'] = min(5, target.resources.get('chi', 0) + 1)

def monk_stance_regen(ctx):
    entity = ctx.get('entity')
    effects = getattr(entity, 'status_effects', {})
    
    if "crane_stance" in effects:
        entity.resources['chi'] = min(5, entity.resources.get('chi', 0) + 1)
        if 'momentum' in entity.resources:
            entity.resources['momentum'] = min(100, entity.resources.get('momentum', 0) + 2)
    if "tiger_stance" in effects:
        entity.resources['stamina'] = min(entity.get_max_resource('stamina'), entity.resources.get('stamina', 0) + 5)
    if "turtle_stance" in effects:
        entity.resources['concentration'] = min(entity.get_max_resource('concentration'), entity.resources.get('concentration', 0) + 3)

def black_mage_cost(ctx):
    player = ctx.get('player')
    if getattr(player, 'active_class', None) == 'black_mage':
        if 'costs' in ctx:
            if ctx['costs']['stamina'] > 0: ctx['costs']['stamina'] = int(ctx['costs']['stamina'] * 1.20)
            if ctx['costs']['concentration_percent'] > 0: ctx['costs']['concentration_percent'] = int(ctx['costs']['concentration_percent'] * 1.20)

def red_mage_momentum(ctx):
    player = ctx.get('player')
    skill = ctx.get('skill')
    if getattr(player, 'active_class', None) == 'red_mage':
        if "spell" in skill.identity_tags:
            player.resources['momentum'] = min(100, player.resources.get('momentum', 0) + 1)

def red_mage_melee_concentration(ctx):
    attacker = ctx.get('attacker')
    if getattr(attacker, 'active_class', None) == 'red_mage':
        attacker.resources['concentration'] = min(attacker.get_max_resource('concentration'), attacker.resources.get('concentration', 0) + 1)
