import logging
from utilities.colors import Colors
from logic.constants import Tags
from logic.core import resource_engine
from logic.core import status_effects_engine

logger = logging.getLogger("GodlessMUD")

def calculate_synergies(player):
    """
    Scans player's equipped blessings to determine active Synergies.
    Updates player.active_synergies and player.synergy_bonuses.
    """
    # Use Global Tag Count (GTC) from ResonanceAuditor if available to include Gear/Effects
    if hasattr(player, 'current_tags') and player.current_tags:
        tag_counts = player.current_tags
    else:
        # Fallback to just blessings (Deck) if GTC not calculated yet
        tag_counts = {}
        for b_id in player.equipped_blessings:
            blessing = player.game.world.blessings.get(b_id)
            if not blessing: continue
            for tag in blessing.identity_tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
            
    active_synergies = []
    bonuses = {}
    
    for s_id, synergy in player.game.world.synergies.items():
        match = True
        reqs = getattr(synergy, 'requirements', {})
        if not reqs: continue
        
        for req_tag, req_count in reqs.items():
            # Ensure we are reading a flat dictionary (tag: int)
            if not isinstance(req_count, int):
                continue

            if tag_counts.get(req_tag, 0) < req_count:
                match = False
                break
        
        if match:
            active_synergies.append(s_id)
            for stat, val in synergy.bonuses.items():
                if stat == 'passive':
                    continue
                try:
                    val_int = int(val)
                    bonuses[stat] = bonuses.get(stat, 0) + val_int
                except ValueError:
                    logger.warning(f"Invalid synergy bonus value for {s_id} ({stat}): {val}")
                
    player.active_synergies = active_synergies
    player.synergies = {s_id: True for s_id in active_synergies} # Map for O(1) lookup (e.g. [CHAIN_CAST])
    player.synergy_bonuses = bonuses

def on_blessing_cast(player, blessing):
    """Hook called when a blessing is cast to trigger synergy effects."""
    # Red Mage: Martial casts build Crimson Charges
    if player.synergies.get('red_mage'):
        if "martial" in blessing.identity_tags:
            if player.crimson_charges < 3:
                player.crimson_charges += 1
                player.send_line(f"{Colors.RED}[SYNERGY] Your blade hums with crimson energy.{Colors.RESET}")

def apply_combat_synergies(attacker, target, blessing, attack_tags, damage):
    """
    Central handler for Synergy/Class effects triggered during combat execution.
    Replaces hardcoded logic in combat_actions.py.
    """
    if not hasattr(attacker, 'synergies'): return

    # --- RED MAGE MECHANICS ---
    if attacker.synergies.get('red_mage'):
        # 1. Stability/Concentration Refund (Replaces standard Martial refund)
        if damage > 0 and Tags.MARTIAL in attack_tags:
            resource_engine.modify_resource(attacker, Tags.CONCENTRATION, 4, source="Red Mage", context="Refund", log=True)

        # 2. Spellstrike (Concentration Refund)
        # Metadata: "synergy_type": "concentration_refund", "synergy_value": 10
        if blessing and getattr(blessing, 'metadata', {}).get('synergy_type') == 'concentration_refund':
            amount = blessing.metadata.get('synergy_value', 10)
            resource_engine.modify_resource(attacker, Tags.CONCENTRATION, amount, source=blessing.name, context="Synergy")
            if hasattr(attacker, 'send_line'):
                attacker.send_line(f"{Colors.MAGENTA}[CHAIN_CAST] {blessing.name} restores {amount} Concentration!{Colors.RESET}")
        
        # 3. Mend Blade (Status Purge)
        # Metadata: "synergy_type": "status_purge"
        if blessing and getattr(blessing, 'metadata', {}).get('synergy_type') == 'status_purge':
            if attacker.status_effects:
                # Find a debuff to purge (Safe Purge)
                game = getattr(attacker, 'game', None)
                eff_to_remove = None
                
                for eff_id in list(attacker.status_effects.keys()):
                    eff_def = status_effects_engine.get_effect_definition(eff_id, game)
                    if eff_def and eff_def.get('metadata', {}).get('is_debuff'):
                        eff_to_remove = eff_id
                        break
                
                if eff_to_remove:
                    status_effects_engine.remove_effect(attacker, eff_to_remove)
                    if hasattr(attacker, 'send_line'):
                        attacker.send_line(f"{Colors.MAGENTA}[CHAIN_CAST] {blessing.name} purges {eff_to_remove}!{Colors.RESET}")


def on_combat_hit(player, attack_tags):
    """Hook called when a player lands a hit."""
    if not hasattr(player, 'synergies'): return
    if player.synergies.get('red_mage'):
        if "martial" in attack_tags:
            if player.crimson_charges < 3:
                player.crimson_charges += 1
                player.send_line(f"{Colors.RED}[SYNERGY] Your blade hums with crimson energy.{Colors.RESET}")