from logic.core import event_engine
from utilities.colors import Colors
from logic.constants import Tags

def on_build_prompt(ctx):
    player = ctx.get('player')
    prompts = ctx.get('prompts')

    if getattr(player, 'active_class', None) == 'red_mage':
        res = getattr(player, 'crimson_charges', 0)
        prompts.append(f"{Colors.RED}CHARGES: {res}/3{Colors.RESET}")

def on_blessing_cast(ctx):
    """Handles Crimson Charge consumption and penalties for Red Mages."""
    player = ctx.get('player')
    blessing = ctx.get('skill')

    if getattr(player, 'active_class', None) != 'red_mage':
        return

    # Use actual synergies/tags for logic
    is_spell = any(t in blessing.identity_tags for t in [Tags.MAGIC, Tags.ELEMENTAL, Tags.ARCANE, Tags.HOLY, Tags.DARK, Tags.SORCERY])
    is_martial = Tags.MARTIAL in blessing.identity_tags

    if is_spell and not is_martial:
        charges = getattr(player, 'crimson_charges', 0)
        if charges > 0:
            player.crimson_charges = charges - 1
            player.send_line(f"{Colors.RED}[SYNERGY] Crimson Charge consumed! Instant Cast! (+20% Potency){Colors.RESET}")
        else:
            # Cold Mana Penalty
            player.send_line(f"{Colors.YELLOW}Your mana is cold! The spell resists your call...{Colors.RESET}")
            if hasattr(player, 'cooldowns'):
                current_cd = player.cooldowns.get(blessing.id, player.game.tick_count)
                player.cooldowns[blessing.id] = max(current_cd, player.game.tick_count + 2) 

def register_events():
    event_engine.subscribe('on_build_prompt', on_build_prompt)
    event_engine.subscribe('magic_on_blessing_cast', on_blessing_cast)
