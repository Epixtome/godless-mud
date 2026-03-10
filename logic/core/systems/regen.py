from logic.core import event_engine, resources
from logic.constants import Tags
from utilities.colors import Colors

def passive_regen(game):
    """Heartbeat task for HP, Stamina, Concentration, and Charge regeneration."""
    for player in list(game.players.values()):
        # Modular Hook for periodic mechanics (Sync, Stances, etc)
        event_engine.dispatch("on_combat_tick", player=player)
        
        # Delegate to Resource Engine
        resources.process_tick(player)

        # Charge Regen (1 per 2 ticks)
        if game.tick_count % 2 == 0:
            if hasattr(player, 'blessing_charges') and player.blessing_charges:
                for b_id in list(player.blessing_charges.keys()):
                    blessing = game.world.blessings.get(b_id)
                    if blessing and hasattr(blessing, 'charges'):
                        max_c = blessing.charges
                        if player.blessing_charges[b_id] < max_c:
                            player.blessing_charges[b_id] += 1

    # Mob Regen & Mechanics
    for room in game.world.rooms.values():
        for mob in room.monsters:
            # Standard Regen
            if mob.hp < mob.max_hp and not mob.fighting:
                mob.hp = min(mob.max_hp, mob.hp + 1)
            
            # Resource Regen for AI
            if hasattr(mob, 'resources'):
                max_conc = mob.get_max_resource(Tags.CONCENTRATION)
                mob.resources[Tags.CONCENTRATION] = min(max_conc, mob.resources.get(Tags.CONCENTRATION, 0) + 5)
                
                # Heat Decay
                mob.resources[Tags.HEAT] = max(0, mob.resources.get(Tags.HEAT, 0) - 5)

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
                            part['hp'] = max_part_hp
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
