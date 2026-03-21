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
    player_class = getattr(combatant, 'active_class', None)
    
    if "whirlwind" in deck or player_class == 'barbarian':
        is_tanking = target and target.fighting == combatant
        if is_tanking:
            if player_class == 'barbarian':
                from logic.core import resources
                resources.modify_resource(combatant, 'fury', 5, source="Combat", context="Tanking")
            else:
                current = combatant.resources.get('momentum', 0)
                combatant.resources['momentum'] = min(10, current + 1)


def black_mage_cost(ctx):
    player = ctx.get('player')
    if getattr(player, 'active_class', None) == 'black_mage':
        if 'costs' in ctx:
            if ctx['costs'].get('stamina', 0) > 0: ctx['costs']['stamina'] = int(ctx['costs']['stamina'] * 1.20)
            if ctx['costs'].get('concentration', 0) > 0: ctx['costs']['concentration'] = int(ctx['costs']['concentration'] * 1.20)

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

def handle_posture_recovery(ctx):
    """Event listener to restore Balance to 100 when Off Balance expires."""
    from utilities.colors import Colors
    entity = ctx.get('player') or ctx.get('entity')
    status_id = ctx.get('status_id') or ctx.get('effect_id')

    if status_id == "off_balance" and hasattr(entity, 'resources'):
        entity.resources['balance'] = 100
        if hasattr(entity, 'send_line'):
            entity.send_line(f"{Colors.CYAN}You have recovered your posture.{Colors.RESET}")
        
        # Broadcast to room so attacker sees it
        if hasattr(entity, 'room') and entity.room:
            entity.room.broadcast(f"{entity.name} regains their footing.", exclude_player=entity)
